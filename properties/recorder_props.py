from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import Context, PropertyGroup, Scene

from ..bpy_register import bpy_register_property


@bpy_register_property(Scene, "ow_recorder_props")
class OWRecorderProperties(PropertyGroup):
    hide_player_model: BoolProperty(
        name="Hide player model",
        default=True,
        options=set(),
    )

    record_hdri: BoolProperty(
        name="Record HDRI",
        description="Record a 360 video from Outer Wilds and use it in world shader node tree. The video is recorded from 'HDRI Pivot' point",
        default=False,
    )

    record_depth: BoolProperty(
        name="Record depth",
        description="Record a video from the Free Camera's depth texture in Outer Wilds. Use it in the compositor node tree",
        default=False,
    )

    hdri_face_size: IntProperty(
        name="HDRI face size",
        description="HDRI is recorded as a 360 video, made of 6 rectangular parts (faces). This setting controls size of these faces. Increase for higher HDRI quality",
        default=1024,
        min=10,
        options=set(),
    )

    animation_chunk_size: IntProperty(
        name="Animation chunk size",
        description="How much keyframes at a time will be sent to Outer Wilds. Increase for less recording time but higher memory usage",
        default=50,
        min=1,
        options=set(),
    )

    modal_timer_delay: FloatProperty(
        name="Modal delay",
        description="Time interval in seconds. Controls how frequently the addon will send data to Outer Wilds. Increase for better performance but slower recording time",
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
    def from_context(context: Context) -> "OWRecorderProperties":
        return context.scene.ow_recorder_props

