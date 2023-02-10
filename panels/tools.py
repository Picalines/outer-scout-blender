from bpy.types import Panel

from ..bpy_register import bpy_register
from ..operators.synchronize import OW_RECORDER_OT_synchronize
from ..operators.create_ow_pivots import OW_RECORDER_OT_create_ow_pivots


@bpy_register
class OW_RECORDER_PT_tools(Panel):
    bl_idname = 'OW_RECORDER_PT_tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Outer Wilds Recorder'
    bl_label = 'Tools'

    def draw(self, _):
        self.layout.operator(
            operator=OW_RECORDER_OT_synchronize.bl_idname,
            icon='UV_SYNC_SELECT',
            text='Sync with Outer Wilds',
        )

        self.layout.operator(
            operator=OW_RECORDER_OT_create_ow_pivots.bl_idname,
            icon='OUTLINER_OB_EMPTY',
            text='Create pivots',
        )
