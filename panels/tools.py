from bpy.types import Panel

from ..bpy_register import bpy_register
from ..properties import OWRecorderReferencePropertis
from ..operators import OW_RECORDER_OT_synchronize, OW_RECORDER_OT_create_ow_pivots


@bpy_register
class OW_RECORDER_PT_tools(Panel):
    bl_idname = "OW_RECORDER_PT_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Outer Wilds Recorder"
    bl_label = "Tools"

    def draw(self, context):
        reference_props = OWRecorderReferencePropertis.from_context(context)

        self.layout.operator(
            operator=OW_RECORDER_OT_synchronize.bl_idname,
            icon="UV_SYNC_SELECT",
            text="Sync with Outer Wilds",
        )

        if not reference_props.hdri_pivot:
            self.layout.operator(
                operator=OW_RECORDER_OT_create_ow_pivots.bl_idname,
                icon="OUTLINER_OB_EMPTY",
                text="Create pivots",
            )
