from bpy.types import Panel

from ..operators.synchronize import OW_RECORDER_OT_synchronize


class OW_RECORDER_PT_sync_tools(Panel):
    bl_idname = 'OW_RECORDER_PT_sync_tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Outer Wilds Recorder'
    bl_label = 'Synchronize'

    def draw(self, _):
        self.layout.operator(
            operator=OW_RECORDER_OT_synchronize.bl_idname,
            icon='UV_SYNC_SELECT',
            text='Sync with Outer Wilds',
        )
