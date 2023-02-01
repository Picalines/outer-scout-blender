import bpy
from bpy.types import Operator, Object, Context

import os
import subprocess
from pathlib import Path

from ..preferences import OWRecorderPreferences
from .ground_body_selection_helper import GroundBodySelectionHelper


GROUND_BODY_COLLECTION_NAME = 'Outer Wilds ground body'


def get_current_ground_body() -> Object | None:
    if GROUND_BODY_COLLECTION_NAME not in bpy.data.collections:
        return None
    ground_body_collection = bpy.data.collections[GROUND_BODY_COLLECTION_NAME]
    return ground_body_collection.objects[0] if any(ground_body_collection.objects) else None


class OW_RECORDER_OT_load_ground_body(Operator, GroundBodySelectionHelper):
    '''Loads current ground body (might take a while for the first time) and links it to current project.'''

    bl_idname = 'ow_recorder.load_ground_body'
    bl_label = 'Load ground body'

    @classmethod
    def poll(cls, _) -> bool:
        return get_current_ground_body() is None

    def execute(self, context: Context):
        if GROUND_BODY_COLLECTION_NAME in bpy.data.collections:
            context.view_layer.objects.active = bpy.data.collections[GROUND_BODY_COLLECTION_NAME].objects[0]
            return {'FINISHED'}

        preferences = OWRecorderPreferences.from_context(context)
        if preferences.empty():
            self.report({'ERROR'}, 'plugin preferences are empty')
            return {'CANCELLED'}

        ground_body_name = self.get_ground_body_name(preferences)
        if ground_body_name is None:
            self.report({'ERROR'}, 'could not get current ground body name')
            return {'CANCELLED'}

        ground_body_project_path = Path(preferences.ow_bodies_folder).joinpath(ground_body_name + '.blend')

        if not ground_body_project_path.exists():
            return_code = self._generate_ground_body_file_in_new_instance(ground_body_name)
            if not (return_code == 0 and ground_body_project_path.exists()):
                self.report({'ERROR'}, 'could not generate ground body .blend file')
                return {'CANCELLED'}

        had_body_link = (ground_body_name + '.blend') in bpy.data.libraries

        ground_body_project_path = str(ground_body_project_path)
        collection_name = f'{ground_body_name} Collection'
        ground_body_project_import_status = bpy.ops.wm.link(
            filepath=os.path.join(ground_body_project_path, 'Collection', collection_name),
            filename=collection_name,
            directory=os.path.join(ground_body_project_path, 'Collection'))

        if ground_body_project_import_status != {'FINISHED'}:
            self.report({'ERROR'}, 'could not link ground body .blend file')
            return {'CANCELLED'}

        if had_body_link:
            ground_body_link = bpy.data.objects[ground_body_name]
            ground_body_link: Object = ground_body_link.copy()
            ground_body_link.parent = None
            context.scene.collection.objects.link(ground_body_link)
            context.view_layer.objects.active = ground_body_link

        ground_body_link = context.view_layer.objects.active
        ground_body_link.hide_render = True

        if not had_body_link:
            ground_body_link.name = ground_body_name

        ground_body_collection = bpy.data.collections.new(GROUND_BODY_COLLECTION_NAME)
        context.scene.collection.children.link(ground_body_collection)
        ground_body_collection.objects.link(ground_body_link)
        context.scene.collection.objects.unlink(ground_body_link)
        ground_body_collection.hide_render = True

        return {'FINISHED'}

    def _generate_ground_body_file_in_new_instance(self, ground_body_name: str) -> int:
        python_expr = f"import sys, bpy; bpy.ops.ow_recorder.generate_ground_body_background(ground_body='{ground_body_name}')"
        cmd = f'"{bpy.app.binary_path}" -noaudio --background --log-level -1 --python-expr "{python_expr}"'

        process = subprocess.run(cmd, shell=False, creationflags=subprocess.CREATE_NEW_CONSOLE)
        return process.returncode
