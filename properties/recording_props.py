from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty
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

    animation_chunk_size: IntProperty(
        name="Animation Chunk Size",
        description="How much keyframes at a time will be sent to Outer Wilds",
        default=50,
        min=1,
        options=set(),
    )

    modal_timer_delay: FloatProperty(
        name="Modal Delay",
        description="Time interval in seconds. Controls how frequently the addon will send data to Outer Wilds",
        default=0.1,
        min=0.001,
        options=set(),
    )

    is_recording: BoolProperty(
        default=False,
        options=set(),
    )

    stage_description: StringProperty(
        options=set(),
    )

    stage_progress: FloatProperty(
        default=0,
        min=0,
        max=1,
        options=set(),
    )

    @staticmethod
    def from_context(context: Context) -> "RecordingProperties":
        return context.scene.outer_scout_recording

