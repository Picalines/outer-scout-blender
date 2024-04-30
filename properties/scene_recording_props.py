from bpy.props import BoolProperty, FloatProperty
from bpy.types import Context, PropertyGroup, Scene

from ..bpy_register import bpy_register_property


@bpy_register_property(Scene, "outer_scout_recording")
class SceneRecordingProperties(PropertyGroup):
    modal_timer_delay: FloatProperty(
        name="Modal Delay",
        description="Time interval in seconds. Controls how often the addon will ask Outer Wilds about the recording progress",
        default=0.1,
        min=0.001,
        options=set(),
    )

    in_progress: BoolProperty(
        default=False,
        options=set(),
    )

    progress: FloatProperty(
        default=0,
        min=0,
        max=1,
        options=set(),
    )

    @staticmethod
    def from_context(context: Context) -> "SceneRecordingProperties":
        return context.scene.outer_scout_recording

