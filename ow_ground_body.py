import os
import subprocess
from mathutils import Quaternion
from math import radians
from pathlib import Path
from glob import glob

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator, Object, Scene

from .ui_utils import show_message_popup
from .object_utils import create_empty, get_child_by_path, iter_parents
from .preferences import OWSceneImporterPreferences
from .ow_json_data import OWSceneData, OWMeshesData, load_ow_json_data, apply_transform_data


def load_ground_body(owscene_filepath: str, preferences: OWSceneImporterPreferences, scene: Scene, ow_data: OWSceneData) -> Object | None:
    ground_body_name = ow_data['ground_body']['name']

    ground_body_project_path = Path(preferences.ow_bodies_folder).joinpath(ground_body_name + '.blend')

    if not ground_body_project_path.exists():
        return_code = generate_ground_body_file_in_new_instance(owscene_filepath)
        if not (return_code == 0 and ground_body_project_path.exists()):
            return None

    had_body_link = (ground_body_name + '.blend') in bpy.data.libraries

    ground_body_project_path = str(ground_body_project_path)
    ground_body_project_import_status = bpy.ops.wm.link(
        filepath=os.path.join(ground_body_project_path, 'Collection', 'Collection'),
        filename='Collection',
        directory=os.path.join(ground_body_project_path, 'Collection'))

    if ground_body_project_import_status != {'FINISHED'}:
        return None

    if had_body_link:
        ground_body_link = bpy.data.objects[ground_body_name]
        ground_body_link: Object = ground_body_link.copy()
        ground_body_link.parent = None
        scene.collection.objects.link(ground_body_link)
        bpy.context.view_layer.objects.active = ground_body_link

    ground_body_link = bpy.context.view_layer.objects.active
    ground_body_link.hide_render = True

    if not had_body_link:
        ground_body_link.name = ground_body_name

    apply_transform_data(ground_body_link, ow_data['ground_body']['transform'])

    return ground_body_link


def generate_ground_body_file_in_new_instance(owscene_filepath: str):
    python_expr = f"import sys, bpy; bpy.ops.outer_wilds_recorder.generate_ground_body_background(filepath=sys.argv[-1])"
    cmd = f'"{bpy.app.binary_path}" -noaudio --background --log-level -1 --python-expr "{python_expr}" -- {owscene_filepath}'

    show_message_popup(bpy.context, 'Generating .blend of ground body. This may take a while...', icon='TIME')

    process = subprocess.run(cmd, shell=False)
    return process.returncode


class OWGroundBodyGenerator(Operator, ImportHelper):
    bl_idname = 'outer_wilds_recorder.generate_ground_body'
    bl_label = 'Generate .blend from extracted .fbx ground body with higher resolution'

    filter_glob: StringProperty(
        default='*.owscene',
        options={'HIDDEN'}
    )

    def execute(self, context):
        preferences: OWSceneImporterPreferences = context.preferences.addons[__package__].preferences

        self.log('INFO', 'loading scene data json')
        ow_data = load_ow_json_data(self.filepath, OWSceneData)
        ground_body_name = ow_data['ground_body']['name']

        self.log('INFO', 'loading meshes data json')
        try:
            ow_meshes_path = glob(f'{ground_body_name}_meshes_*.json', root_dir=preferences.ow_bodies_folder, recursive=False)[0]
            ow_meshes_path = str(Path(preferences.ow_bodies_folder).joinpath(ow_meshes_path))
        except IndexError:
            self.log('ERROR', f'meshes list for {ground_body_name} not found in {preferences.ow_bodies_folder}')
            return {'CANCELED'}

        ow_meshes_data = load_ow_json_data(ow_meshes_path, OWMeshesData)

        self.log('INFO', 'importing fbx')
        ground_body_fbx_path = str(Path(preferences.ow_bodies_folder).joinpath(ground_body_name + '.fbx'))
        fbx_import_status = bpy.ops.import_scene.fbx(filepath=ground_body_fbx_path)
        if fbx_import_status != {'FINISHED'}:
            self.log('ERROR', f'failed to import ground body fbx: {ground_body_fbx_path}')
            return {'CANCELED'}

        extracted_ground_body_obj = bpy.data.objects[ground_body_name]
        extracted_ground_body_obj.name += '_extracted'

        bpy.ops.object.select_all(action='DESELECT')
        for parent in iter_parents(extracted_ground_body_obj):
            parent.select_set(state=True)
        bpy.ops.object.delete()

        plain_meshes_count = len(ow_meshes_data['plain_meshes'])
        streamed_meshes_count = len(ow_meshes_data['streamed_meshes'])

        ignored_object_name_parts: list[str] = preferences.ignored_objects.split(',')

        for i, plain_mesh_data in enumerate(ow_meshes_data['plain_meshes'], start=1):
            self.log('INFO', f'placing plain mesh [{i}/{plain_meshes_count}] from {plain_mesh_data["game_object_path"]}')

            mesh_path = plain_mesh_data['game_object_path'].split('/')[1:]

            skip_object = False
            for banned_object in ignored_object_name_parts:
                if banned_object.lower() in mesh_path[-1].lower():
                    skip_object = True
                    break

            if skip_object:
                self.log('INFO', f'skipped plain mesh at {plain_mesh_data["game_object_path"]}')
                continue

            extracted_child = get_child_by_path(extracted_ground_body_obj, mesh_path, mask_duplicates=True)
            if extracted_child is None:
                self.log('WARNING', f'missing plain mesh child at {plain_mesh_data["game_object_path"]}')
                continue

            extracted_child.parent = None
            apply_transform_data(extracted_child, plain_mesh_data['transform'])
            extracted_child.rotation_quaternion @= Quaternion((0, 1, 0), radians(90))

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = extracted_ground_body_obj
        bpy.ops.object.select_grouped(extend=True, type='CHILDREN_RECURSIVE')
        bpy.ops.object.delete()

        imported_objs: dict[str, Object] = {}

        for i, streamed_mesh_data in enumerate(ow_meshes_data['streamed_meshes'], start=1):
            self.log('INFO', f'loading streamed mesh [{i}/{streamed_meshes_count}]')

            obj_path = Path(preferences.ow_assets_folder).joinpath(streamed_mesh_data['asset_path'].removesuffix('.asset') + '.obj')
            if not obj_path.exists():
                self.log('WARNING', f'missing streamed mesh obj file at {obj_path}')
                continue

            obj_path = str(obj_path)

            if obj_path not in imported_objs:
                obj_import_status = bpy.ops.wm.obj_import(filepath=obj_path)
                if obj_import_status != {'FINISHED'}:
                    self.log('ERROR', f'failed to import streamed mesh obj at {obj_path}')
                    continue

                loaded_mesh = bpy.data.objects[bpy.context.view_layer.objects.active.name]
                imported_objs[obj_path] = loaded_mesh
            else:
                loaded_mesh = imported_objs[obj_path].copy()
                imported_objs[obj_path].users_collection[0].objects.link(loaded_mesh)

            loaded_mesh.parent = None
            apply_transform_data(loaded_mesh, streamed_mesh_data['transform'])
            loaded_mesh.rotation_quaternion @= Quaternion((0, 1, 0), radians(90))

        self.log('INFO', 'creating body pivot object')
        ground_body_obj = create_empty()
        ground_body_obj.name = ground_body_name
        apply_transform_data(ground_body_obj, ow_meshes_data['body']['transform'])

        self.log('INFO', 'parenting objects to pivot')
        bpy.ops.object.select_all(action='SELECT')
        bpy.context.view_layer.objects.active = ground_body_obj
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

        self.log('INFO', 'resetting pivot transform')
        ground_body_obj.location = (0, 0, 0)
        ground_body_obj.rotation_quaternion = Quaternion()

        return {'FINISHED'}

    def log(self, type: str, message: str):
        print(f'[{type}] {message}')
        self.report({type}, message)


class OWGroundBodyGenerator_Background(Operator, ImportHelper):
    bl_idname = 'outer_wilds_recorder.generate_ground_body_background'
    bl_label = 'Call outer_wilds_recorder.generate_ground_body in background environment'

    filter_glob: StringProperty(
        default='*.owscene',
        options={'HIDDEN'}
    )

    def execute(self, context):
        preferences: OWSceneImporterPreferences = context.preferences.addons[__package__].preferences
        ow_data = load_ow_json_data(self.filepath, OWSceneData)

        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        bpy.ops.outer_wilds_recorder.generate_ground_body(filepath=self.filepath)

        bpy.context.view_layer.update()
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(preferences.ow_bodies_folder).joinpath(ow_data['ground_body']['name'] + '.blend')))

        bpy.ops.wm.quit_blender()
        return {'FINISHED'}
