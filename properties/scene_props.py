from bpy.types import PropertyGroup, Scene, Context
from bpy.props import StringProperty, FloatProperty

from ..bpy_register import bpy_register_property


@bpy_register_property(Scene, "ow_recorder_scene_props")
class OWRecorderSceneProperties(PropertyGroup):
    ground_body_name: StringProperty(
        name="Ground body name",
        description="Outer Wilds ground body name independent of scene object",
        default="",
        options=set(),
    )

    time_scale: FloatProperty(
        name="Time scale",
        description="Use this to animate the Time.timeScale in Outer Wilds",
        default=1,
        min=0,
        options={"ANIMATABLE"},
    )

    @staticmethod
    def from_context(context: Context) -> "OWRecorderSceneProperties":
        return context.scene.ow_recorder_scene_props
