import bpy
from bpy.types import Operator, Object

from mathutils import Matrix
from math import radians
from pathlib import Path
import json

from ..bpy_register import bpy_register
from ..preferences import OWRecorderPreferences
from ..api import APIClient
from ..api.models import TransformModel, GroundBodyMeshInfo
from ..utils import iter_parents, get_child_by_path
from .ground_body_selection_helper import GroundBodySelectionHelper


@bpy_register
class OW_RECORDER_OT_generate_ground_body(Operator, GroundBodySelectionHelper):
    bl_idname = 'ow_recorder.generate_ground_body'
    bl_label = 'Generate .blend from extracted .fbx ground body with higher resolution'

    def execute(self, context):
        preferences = OWRecorderPreferences.from_context(context)
        if preferences.empty():
            self._log('ERROR', 'plugin preferences are empty')
            return {'CANCELLED'}

        ow_assets_folder, ow_bodies_folder = map(Path, (preferences.ow_assets_folder, preferences.ow_bodies_folder))

        api_client = APIClient(preferences)

        ground_body_name = self.get_ground_body_name(api_client)
        if ground_body_name is None:
            self._log('ERROR', 'failed to get ground body name')
            return {'CANCELLED'}

        self._log('INFO', f'generating {ground_body_name} object...')

        mesh_list_path = ow_bodies_folder.joinpath(ground_body_name + '_meshes.json')
        if not mesh_list_path.exists():
            current_ground_body_name = api_client.get_ground_body_name()
            if current_ground_body_name != ground_body_name:
                self._log('ERROR', f'unable to create mesh list file. Go to {ground_body_name} in game and call operator again')
                return {'CANCELLED'}

            self._log('INFO', 'creating mesh list file')
            success = api_client.generate_current_ground_body_mesh_list(str(mesh_list_path))
            if not success:
                self._log('ERROR', 'could not generate mesh list')
                return {'CANCELLED'}

        if not mesh_list_path.exists():
            self._log('ERROR', 'BUG: mesh list was not created by API')
            return {'CANCELLED'}

        self._log('INFO', 'loading mesh list')
        with open(mesh_list_path, 'rb') as ow_meshes_json_file:
            ground_body_meshes_info: GroundBodyMeshInfo = json.loads(ow_meshes_json_file.read())

        imported_ow_objects: dict[str, Object | None] = {
            streamed_mesh['path']: None for sector in ground_body_meshes_info['sectors'] for streamed_mesh in sector['streamed_meshes']
        }

        self._log('INFO', f'importing {len(imported_ow_objects)} .obj files of streamed assets')
        for asset_path in imported_ow_objects:
            try:
                obj_path = str(ow_assets_folder.joinpath(asset_path.removesuffix('.asset') + '.obj'))
                bpy.ops.wm.obj_import(filepath=obj_path)
            except:
                self._log('WARNING', f'failed to import .obj file at {obj_path}')
                continue

            imported_obj_mesh = bpy.data.objects[context.view_layer.objects.active.name]
            if imported_obj_mesh.type != 'EMPTY':
                imported_ow_objects[asset_path] = imported_obj_mesh

        bpy.ops.object.select_all(action='DESELECT')

        ground_body_fbx_path = str(ow_bodies_folder.joinpath(ground_body_name + '.fbx'))
        self._log('INFO', f'importing {ground_body_fbx_path}')
        if bpy.ops.import_scene.fbx(filepath=ground_body_fbx_path) != {'FINISHED'}:
            self._log('ERROR', f'failed to import ground body fbx: {ground_body_fbx_path}')
            return {'CANCELLED'}

        extracted_ground_body_object = bpy.data.objects[ground_body_name]
        extracted_ground_body_object.name += '_extracted'

        self._log('INFO', 'deleting ground body parents')
        for parent in list(iter_parents(extracted_ground_body_object)):
            bpy.data.objects.remove(parent, do_unlink=True)

        self._log('INFO', 'loading sectors')

        ignored_object_name_parts: list[str] = preferences.ignored_objects.split(',')

        ground_body_inverted_matrix = Matrix.Rotation(radians(90), 4, (0, 1, 0)) @ TransformModel.from_json(ground_body_meshes_info['body_transform'])\
            .unity_to_blender()\
            .to_matrix()\
            .inverted()

        sectors_count = len(ground_body_meshes_info['sectors'])

        ground_body_collection = bpy.data.collections.new(f'{ground_body_name} Collection')
        context.scene.collection.children.link(ground_body_collection)

        sector_indices_text = bpy.data.texts.new(f'{ground_body_name} sectors')
        sector_indices_text.use_fake_user = True

        sector_indices_text.write('{\n')

        for sector_index, sector_info in enumerate(ground_body_meshes_info['sectors']):
            self._log('INFO', f"* sector '{sector_info['path']}' [{sector_index + 1}/{sectors_count}]")

            sector_indices_text.write(f'    "{sector_info["path"]}": {sector_index}')
            if (sector_index + 1) < sectors_count:
                sector_indices_text.write(',')
            sector_indices_text.write('\n')

            sector_collection = bpy.data.collections.new(f'{ground_body_name} Sector #{sector_index} Collection')
            ground_body_collection.children.link(sector_collection)

            self._log('INFO', f'placing plain meshes ({len(sector_info["plain_meshes"])} objects)')
            for plain_mesh_info in sector_info['plain_meshes']:
                mesh_path = plain_mesh_info['path'].split('/')[1:]

                skip_object = False
                for banned_object in ignored_object_name_parts:
                    if banned_object.lower() in mesh_path[-1].lower():
                        skip_object = True
                        break

                if skip_object:
                    continue

                extracted_child = get_child_by_path(extracted_ground_body_object, mesh_path, mask_duplicates=True)
                if extracted_child is None:
                    self._log('WARNING', f'missing plain mesh child at {plain_mesh_info["path"]}')
                    continue

                context.collection.objects.unlink(extracted_child)
                sector_collection.objects.link(extracted_child)

                extracted_child.parent = None
                extracted_child.matrix_parent_inverse = Matrix.Identity(4)
                extracted_child.matrix_world = ground_body_inverted_matrix @ TransformModel.from_json(plain_mesh_info['transform'])\
                    .unity_to_blender()\
                    .to_matrix()

            self._log('INFO', f'placing streamed meshes ({len(sector_info["streamed_meshes"])} objects)')
            for streamed_mesh_info in sector_info['streamed_meshes']:
                asset_path = streamed_mesh_info['path']
                if asset_path not in imported_ow_objects:
                    continue

                imported_obj_mesh = imported_ow_objects[asset_path]
                if not imported_obj_mesh:
                    continue

                loaded_mesh = imported_obj_mesh.copy()
                sector_collection.objects.link(loaded_mesh)

                loaded_mesh.parent = None
                loaded_mesh.matrix_parent_inverse = Matrix.Identity(4)
                loaded_mesh.matrix_local = ground_body_inverted_matrix @ TransformModel.from_json(streamed_mesh_info['transform'])\
                    .unity_to_blender()\
                    .to_matrix()

            self._log('INFO', 'deleting empties')
            for object in sector_collection.objects:
                if object.type == 'EMPTY':
                    bpy.data.objects.remove(object, do_unlink=True)

        sector_indices_text.write('}')

        self._log('INFO', f'clearing scene collection ({len(context.scene.collection.objects)} objects)')
        for object in context.scene.collection.objects:
            bpy.data.objects.remove(object, do_unlink=True)

        self._log('INFO', 'finished')
        return {'FINISHED'}

    def _log(self, type: str, message: str):
        print(f'[{type}] {message}')
        # reports don't appear dynamically in console window
        # self.report({type}, message)
