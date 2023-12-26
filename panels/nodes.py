from bpy.types import Panel

from ..bpy_register import bpy_register
from ..operators import OW_RECORDER_OT_generate_compositor_nodes, OW_RECORDER_OT_generate_world_nodes
from ..properties import OWRecorderReferenceProperties


@bpy_register
class OW_RECORDER_PT_world_nodes(Panel):
    bl_idname = "OW_RECORDER_PT_world_nodes"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Outer Wilds Recorder"
    bl_label = "Nodes"

    @classmethod
    def poll(cls, context) -> bool:
        space = context.space_data
        reference_props = OWRecorderReferenceProperties.from_context(context)
        return space.tree_type == "ShaderNodeTree" and all(
            (
                reference_props.hdri_pivot,
                reference_props.hdri_image,
            )
        )

    def draw(self, _):
        self.layout.operator(
            OW_RECORDER_OT_generate_world_nodes.bl_idname,
            text="Generate HDRI",
            icon="NODE_MATERIAL",
        )


@bpy_register
class OW_RECORDER_PT_compositor_nodes(Panel):
    bl_idname = "OW_RECORDER_PT_compositor_nodes"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Outer Wilds Recorder"
    bl_label = "Nodes"

    @classmethod
    def poll(cls, context) -> bool:
        space = context.space_data
        reference_props = OWRecorderReferenceProperties.from_context(context)
        return space.tree_type == "CompositorNodeTree" and all(
            (
                reference_props.ground_body,
                reference_props.background_movie_clip,
            )
        )

    def draw(self, _):
        self.layout.operator(
            OW_RECORDER_OT_generate_compositor_nodes.bl_idname,
            text="Generate Compositor",
            icon="NODE_COMPOSITING",
        )

