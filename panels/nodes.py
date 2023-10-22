from bpy.types import Panel

from ..bpy_register import bpy_register
from ..operators import (
    OW_RECORDER_OT_generate_world_nodes,
    OW_RECORDER_OT_generate_compositor_nodes,
)


@bpy_register
class OW_RECORDER_PT_nodes(Panel):
    bl_idname = "OW_RECORDER_PT_nodes"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Outer Wilds Recorder"
    bl_label = "Nodes"

    def draw(self, _):
        self.layout.operator(
            OW_RECORDER_OT_generate_world_nodes.bl_idname,
            text="Generate HDRI",
            icon="NODE_MATERIAL",
        )

        self.layout.operator(
            OW_RECORDER_OT_generate_compositor_nodes.bl_idname,
            text="Generate Compositor",
            icon="NODE_COMPOSITING",
        )
