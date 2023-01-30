import bpy
from bpy.types import Panel


class OW_RECORDER_PT_sync_tools(Panel):
    bl_idname = 'OW_RECORDER_PT_sync_tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Outer Wilds Recorder'
    bl_label = 'Synchronize'

    def draw(self, context):
        self.layout.label(text='Hello, world!')
