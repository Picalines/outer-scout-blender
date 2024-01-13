from bpy.types import Panel

from ..bpy_register import bpy_register
from ..operators import OW_RECORDER_OT_check_api_status


@bpy_register
class OW_RECORDER_PT_animatable_props(Panel):
    bl_idname = "OW_RECORDER_PT_animatable_props"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Outer Wilds Recorder"
    bl_label = "API status"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 11

    def draw(self, _):
        self.layout.operator(
            operator=OW_RECORDER_OT_check_api_status.bl_idname,
            text="Check API status",
            icon="URL",
        )

