from bpy.types import Object, Panel

from ..bpy_register import bpy_register
from ..properties import ObjectProperties, SceneProperties


@bpy_register
class ObjectPanel(Panel):
    bl_idname = "DATA_PT_outer_scout_object"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Outer Scout"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context) -> bool:
        return SceneProperties.from_context(context).is_scene_created

    def draw(self, context):
        active_object: Object = context.active_object
        scene_props = SceneProperties.from_context(context)
        object_props = ObjectProperties.of_object(active_object)
        transform_props = object_props.transform_props
        layout = self.layout

        layout.use_property_split = True

        if scene_props.ground_body == active_object:
            layout.label(text="This is the ground body object")
            return

        layout.prop(object_props, "unity_object_name")

        if active_object.type != "CAMERA":
            transform_header, transform_panel = layout.panel(f"{self.bl_idname}.transform", default_closed=False)
            transform_header.label(text="Transform Recording")
            if transform_panel:
                transform_panel.prop(transform_props, "recording_path")
                transform_panel.prop(transform_props, "mode", expand=True)

