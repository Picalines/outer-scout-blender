from bpy.types import PropertyGroup, Scene, Context
from bpy.props import BoolProperty, StringProperty, FloatProperty, FloatVectorProperty

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

    has_saved_warp: BoolProperty(
        name="Has saved warp",
        description="True whenever you've saved some location to warp to",
        default=False,
        options=set(),
    )

    warp_ground_body: StringProperty(
        name="Warp ground body",
        description="Ground body to warp to",
        default="",
        options=set(),
    )

    warp_transform: FloatVectorProperty(
        name="Warp transform",
        description="Custom warp transform. Use this to save scene location",
        size=10,  # (*pos, *rot, *scale)
        default=(0,) * 10,
        options=set(),
    )

    @staticmethod
    def from_context(context: Context) -> "OWRecorderSceneProperties":
        return context.scene.ow_recorder_scene_props
