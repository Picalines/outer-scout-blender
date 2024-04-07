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
        object_props = ObjectProperties.of_object(active_object)
        layout = self.layout

        layout.use_property_split = True

        layout.prop(object_props, "transform_recording_path")

        if object_props.has_transform_recording_path:
            layout.prop(object_props, "unity_object_name")
            layout.prop(object_props, "transform_mode", expand=True)

