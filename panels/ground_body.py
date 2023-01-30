import bpy
from bpy.types import Panel
from ..operators.load_ground_body import GROUND_BODY_COLLECTION_NAME


class OW_RECORDER_PT_ground_body(Panel):
    bl_idname = 'OW_RECORDER_PT_ground_body'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Outer Wilds Recorder'
    bl_label = 'Ground Body'

    def draw(self, _):
        ground_body_is_loaded = GROUND_BODY_COLLECTION_NAME in bpy.data.collections
        self.layout.operator('ow_recorder.load_ground_body',
            text='Load ground body' if not ground_body_is_loaded else 'Ground body is loaded',
            emboss=not ground_body_is_loaded)
