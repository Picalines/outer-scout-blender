from bpy.props import BoolProperty, FloatProperty, StringProperty
from bpy.types import Context, PropertyGroup, Scene

from ..bpy_register import bpy_register_property


@bpy_register_property(Scene, "outer_scout_recording")
class RecordingProperties(PropertyGroup):
    output_path: StringProperty(
        name="Output Path",
        description="The path to the folder there the recordings will be saved",
        subtype="DIR_PATH",
        default="",
    )

    modal_timer_delay: FloatProperty(
        name="Modal Delay",
        description="Time interval in seconds. Controls how frequently the addon will send data to Outer Wilds",
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
    def from_context(context: Context) -> "RecordingProperties":
        return context.scene.outer_scout_recording

