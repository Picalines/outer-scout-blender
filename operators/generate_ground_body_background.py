import bpy
from bpy.types import Operator

from pathlib import Path

from ..preferences import OWRecorderPreferences


class OW_RECORDER_OT_generate_ground_body_background(Operator):
    bl_idname = 'ow_recorder.generate_ground_body_background'
    bl_label = 'Call ow_recorder.generate_ground_body in background environment'

    def execute(self, context):
        preferences = OWRecorderPreferences.from_context(context)

        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        for c in context.scene.collection.children:
            context.scene.collection.children.unlink(c)

        result = bpy.ops.ow_recorder.generate_ground_body()
        if result != {'FINISHED'}:
            return {'CANCELLED'}

        context.view_layer.update()
        ground_body_object = context.view_layer.objects.active

        ground_body_collection = bpy.data.collections.new(f'{ground_body_object.name} Collection')
        context.scene.collection.children.link(ground_body_collection)

        ground_body_collection.objects.link(ground_body_object)
        for child in ground_body_object.children_recursive:
            ground_body_collection.objects.link(child)
            context.scene.collection.objects.unlink(child)

        bpy.ops.wm.save_as_mainfile(filepath=str(Path(preferences.ow_bodies_folder).joinpath(ground_body_object.name + '.blend')))

        bpy.ops.wm.quit_blender()
        return {'FINISHED'}
