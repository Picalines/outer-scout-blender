import bpy
from bpy.types import Operator, Object

from mathutils import Matrix
from math import radians
from pathlib import Path
import json

from ..preferences import OWRecorderPreferences
from ..api import APIClient
from ..api.models import TransformModel, GroundBodyMeshInfo
from ..utils import iter_parents, get_child_by_path
from .ground_body_selection_helper import GroundBodySelectionHelper


class OW_RECORDER_OT_generate_ground_body(Operator, GroundBodySelectionHelper):
    bl_idname = 'ow_recorder.generate_ground_body'
    bl_label = 'Generate .blend from extracted .fbx ground body with higher resolution'

    def execute(self, context):
        preferences = OWRecorderPreferences.from_context(context)
        if preferences.empty():
            self._log('ERROR', 'plugin preferences are empty')
            return {'CANCELLED'}

        api_client = APIClient(preferences)

        ground_body_name = self.get_ground_body_name(api_client)
        if ground_body_name is None:
            self._log('ERROR', 'failed to get ground body name')
            return {'CANCELLED'}

        self._log('INFO', f'generating {ground_body_name} object...')

        mesh_list_path = Path(preferences.ow_bodies_folder).joinpath(ground_body_name + '_meshes.json')
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

        ground_body_fbx_path = str(Path(preferences.ow_bodies_folder).joinpath(ground_body_name + '.fbx'))
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

        ground_body_inverted_matrix = Matrix.Rotation(radians(90), 4, (1, 0, 0)) @ TransformModel.from_json(ground_body_meshes_info['body_transform'])\
            .unity_to_blender()\
            .to_matrix()\
            .inverted()

        sectors_count = len(ground_body_meshes_info['sectors'])

        ow_assets_folder = Path(preferences.ow_assets_folder)
        imported_objs: dict[str, Object] = {}

        ground_body_collection = bpy.data.collections.new(f'{ground_body_name} Collection')
        context.scene.collection.children.link(ground_body_collection)

        for sector_index, sector_info in enumerate(ground_body_meshes_info['sectors'], start=1):
            self._log('INFO', f"--- SECTOR '{sector_info['path']}' [{sector_index}/{sectors_count}] ---")

            sector_collection = bpy.data.collections.new(f'{sector_info["path"]} Sector Collection')
            ground_body_collection.children.link(sector_collection)

            plain_meshes_count = len(sector_info['plain_meshes'])
            streamed_meshes_count = len(sector_info['streamed_meshes'])

            for plain_mesh_index, plain_mesh_info in enumerate(sector_info['plain_meshes'], start=1):
                mesh_path = plain_mesh_info['path'].split('/')[1:]

                skip_object = False
                for banned_object in ignored_object_name_parts:
                    if banned_object.lower() in mesh_path[-1].lower():
                        skip_object = True
                        break

                if skip_object:
                    continue

                self._log('INFO', f'placing plain mesh [{plain_mesh_index}/{plain_meshes_count}] from {plain_mesh_info["path"]}')

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

            for streamed_mesh_index, streamed_mesh_info in enumerate(sector_info['streamed_meshes'], start=1):
                self._log('INFO', f'loading streamed mesh [{streamed_mesh_index}/{streamed_meshes_count}]')

                asset_path = streamed_mesh_info['path']

                if asset_path not in imported_objs:
                    obj_path = ow_assets_folder.joinpath(streamed_mesh_info['path'].removesuffix('.asset') + '.obj')

                    if not obj_path.exists():
                        self._log('WARNING', f'missing streamed mesh .obj file at {obj_path}')
                        continue

                    obj_import_status = bpy.ops.wm.obj_import(filepath=str(obj_path))

                    if obj_import_status != {'FINISHED'}:
                        self._log('ERROR', f'failed to import streamed mesh .obj at {obj_path}')
                        continue

                    loaded_mesh = bpy.data.objects[context.view_layer.objects.active.name]
                    context.scene.collection.objects.unlink(loaded_mesh)
                    sector_collection.objects.link(loaded_mesh)
                    imported_objs[asset_path] = loaded_mesh
                else:
                    loaded_mesh = imported_objs[asset_path].copy()
                    sector_collection.objects.link(loaded_mesh)

                loaded_mesh.parent = None
                loaded_mesh.matrix_parent_inverse = Matrix.Identity(4)
                loaded_mesh.matrix_local = ground_body_inverted_matrix @ TransformModel.from_json(streamed_mesh_info['transform'])\
                    .unity_to_blender()\
                    .to_matrix()

            self._log('INFO', 'deleting empties from current sector')
            for object in sector_collection.objects:
                if object.type == 'EMPTY':
                    bpy.data.objects.remove(object, do_unlink=True)

        self._log('INFO', 'deleting objects from fbx')
        for child in extracted_ground_body_object.children_recursive:
            bpy.data.objects.remove(child, do_unlink=True)
        bpy.data.objects.remove(extracted_ground_body_object, do_unlink=True)

        self._log('INFO', 'clearing scene collection')
        for object in context.scene.collection.objects:
            context.scene.collection.objects.unlink(object)

        self._log('INFO', 'finished')
        return {'FINISHED'}

    def _log(self, type: str, message: str):
        print(f'[{type}] {message}')
        # reports don't appear dynamically in console window
        # self.report({type}, message)
