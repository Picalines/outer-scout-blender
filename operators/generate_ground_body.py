import bpy
from bpy.types import Operator, Object

from mathutils import Quaternion
from math import radians
from pathlib import Path
import json

from ..preferences import OWRecorderPreferences
from ..api import APIClient
from ..api.models import TransformModel, GroundBodyMeshInfo
from ..utils import iter_parents, get_child_by_path, create_empty
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

        ow_meshes_path = Path(preferences.ow_bodies_folder).joinpath(ground_body_name + '_meshes.json')
        if not ow_meshes_path.exists():
            current_ground_body_name = api_client.get_ground_body_name()
            if current_ground_body_name != ground_body_name:
                self._log('ERROR', f'unable to create mesh list file. Go to {ground_body_name} in game and call operator again')
                return {'CANCELLED'}

            self._log('INFO', 'creating mesh list file')
            success = api_client.generate_current_ground_body_mesh_list(str(ow_meshes_path))
            if not success:
                self._log('ERROR', 'could not generate mesh list')
                return {'CANCELLED'}

        if not ow_meshes_path.exists():
            self._log('ERROR', 'BUG: mesh list was not created by API')
            return {'CANCELLED'}

        self._log('INFO', 'loading mesh list')
        with open(ow_meshes_path, 'rb') as ow_meshes_json_file:
            ow_meshes_data: GroundBodyMeshInfo = json.loads(ow_meshes_json_file.read())

        ground_body_fbx_path = str(Path(preferences.ow_bodies_folder).joinpath(ground_body_name + '.fbx'))
        self._log('INFO', f'importing {ground_body_fbx_path}')
        fbx_import_status = bpy.ops.import_scene.fbx(filepath=ground_body_fbx_path)
        if fbx_import_status != {'FINISHED'}:
            self._log('ERROR', f'failed to import ground body fbx: {ground_body_fbx_path}')
            return {'CANCELLED'}

        extracted_ground_body_obj = bpy.data.objects[ground_body_name]
        extracted_ground_body_obj.name += '_extracted'

        bpy.ops.object.select_all(action='DESELECT')
        for parent in iter_parents(extracted_ground_body_obj):
            parent.select_set(state=True)
        bpy.ops.object.delete()

        plain_meshes_count = len(ow_meshes_data['plain_meshes'])
        streamed_meshes_count = len(ow_meshes_data['streamed_meshes'])

        ignored_object_name_parts: list[str] = preferences.ignored_objects.split(',')

        for i, plain_mesh_info in enumerate(ow_meshes_data['plain_meshes'], start=1):
            self._log('INFO', f'placing plain mesh [{i}/{plain_meshes_count}] from {plain_mesh_info["path"]}')

            mesh_path = plain_mesh_info['path'].split('/')[1:]

            skip_object = False
            for banned_object in ignored_object_name_parts:
                if banned_object.lower() in mesh_path[-1].lower():
                    skip_object = True
                    break

            if skip_object:
                self._log('INFO', f'skipped plain mesh at {plain_mesh_info["path"]}')
                continue

            extracted_child = get_child_by_path(extracted_ground_body_obj, mesh_path, mask_duplicates=True)
            if extracted_child is None:
                self._log('WARNING', f'missing plain mesh child at {plain_mesh_info["path"]}')
                continue

            extracted_child.parent = None
            TransformModel.from_json(plain_mesh_info['transform'])\
                .unity_to_blender()\
                .apply_local(extracted_child)

        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = extracted_ground_body_obj
        bpy.ops.object.select_grouped(extend=True, type='CHILDREN_RECURSIVE')
        bpy.ops.object.delete()

        imported_objs: dict[str, Object] = {}

        for i, streamed_mesh_info in enumerate(ow_meshes_data['streamed_meshes'], start=1):
            self._log('INFO', f'loading streamed mesh [{i}/{streamed_meshes_count}]')

            obj_path = Path(preferences.ow_assets_folder).joinpath(streamed_mesh_info['path'].removesuffix('.asset') + '.obj')
            if not obj_path.exists():
                self._log('WARNING', f'missing streamed mesh obj file at {obj_path}')
                continue

            obj_path = str(obj_path)

            if obj_path not in imported_objs:
                obj_import_status = bpy.ops.wm.obj_import(filepath=obj_path)
                if obj_import_status != {'FINISHED'}:
                    self._log('ERROR', f'failed to import streamed mesh obj at {obj_path}')
                    continue

                loaded_mesh = bpy.data.objects[context.view_layer.objects.active.name]
                imported_objs[obj_path] = loaded_mesh
            else:
                loaded_mesh = imported_objs[obj_path].copy()
                imported_objs[obj_path].users_collection[0].objects.link(loaded_mesh)

            loaded_mesh.parent = None
            TransformModel.from_json(streamed_mesh_info['transform'])\
                .unity_to_blender()\
                .apply_local(loaded_mesh)

        self._log('INFO', 'creating body pivot object')
        ground_body_obj = create_empty()
        ground_body_obj.name = ground_body_name
        TransformModel.from_json(ow_meshes_data['body_transform'])\
            .unity_to_blender()\
            .apply_local(ground_body_obj)

        ground_body_obj.rotation_quaternion @= Quaternion((0, 1, 0), radians(-90))

        self._log('INFO', 'parenting objects to pivot')
        bpy.ops.object.select_all(action='SELECT')
        context.view_layer.objects.active = ground_body_obj
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

        self._log('INFO', 'resetting pivot transform')
        ground_body_obj.location = (0, 0, 0)
        ground_body_obj.rotation_quaternion = Quaternion()

        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = ground_body_obj

        self._log('INFO', 'finished')
        return {'FINISHED'}

    def _log(self, type: str, message: str):
        print(f'[{type}] {message}')
        # self.report({type}, message)
