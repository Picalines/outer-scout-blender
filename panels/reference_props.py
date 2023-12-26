from bpy.types import Panel

from ..bpy_register import bpy_register
from ..operators import OW_RECORDER_OT_create_ow_pivots
from ..properties import OWRecorderReferenceProperties


@bpy_register
class OW_RECORDER_PT_reference_props(Panel):
    bl_idname = "OW_RECORDER_PT_reference_props"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Outer Wilds Recorder"
    bl_label = "Scene References"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 10

    @classmethod
    def poll(cls, context) -> bool:
        reference_props = OWRecorderReferenceProperties.from_context(context)
        return bool(reference_props.ground_body)

    def draw(self, context):
        reference_props = OWRecorderReferenceProperties.from_context(context)

        column = self.layout.column()
        column.enabled = not reference_props.hdri_pivot
        column.operator(
            operator=OW_RECORDER_OT_create_ow_pivots.bl_idname,
            icon="OUTLINER_OB_EMPTY",
            text="Create pivots",
        )

        self.layout.prop(reference_props, "hdri_pivot", text="")

        column = self.layout.column()
        column.enabled = False

        for prop_name in (
            "ground_body",
            "background_movie_clip",
            "hdri_image",
            "depth_movie_clip",
            "hdri_node_tree",
            "compositor_node_tree",
        ):
            column.prop(reference_props, prop_name, text="")

