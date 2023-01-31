import bpy
from bpy.types import Panel
from ..operators.load_ground_body import GROUND_BODY_COLLECTION_NAME


class OW_RECORDER_PT_ground_body(Panel):
    bl_idname = 'OW_RECORDER_PT_ground_body'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Outer Wilds Recorder'
    bl_label = 'Ground Body'

    @classmethod
    def poll(cls, _) -> bool:
        return GROUND_BODY_COLLECTION_NAME not in bpy.data.collections

    def draw(self, _):
        self.layout.operator('ow_recorder.load_ground_body', text='Load ground body', icon='WORLD')
