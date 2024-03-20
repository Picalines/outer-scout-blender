from bpy.types import Panel

from ..operators import CreateSceneOperator

from ..bpy_register import bpy_register
from ..properties import SceneProperties


@bpy_register
class ScenePanel(Panel):
    bl_idname = "DATA_PT_outer_scout_scene"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Outer Scout"
    bl_context = "scene"

    def draw(self, context):
        properties = SceneProperties.from_context(context)

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = True

        if not properties.is_scene_created():
            layout.operator(CreateSceneOperator.bl_idname)
            return

        layout.prop(properties, "origin_parent")

        header, panel = layout.panel(f"{self.bl_idname}.origin", default_closed=True)
        header.label(text="Origin Transform")
        if panel:
            layout.prop(properties, "origin_position")
            layout.prop(properties, "origin_rotation")

