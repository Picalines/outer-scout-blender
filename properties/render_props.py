from bpy.types import PropertyGroup, Context, Scene
from bpy.props import BoolProperty, IntProperty, FloatProperty, StringProperty

from ..bpy_register import bpy_register_property


@bpy_register_property(Scene, "ow_recorder_render_props")
class OWRecorderRenderProperties(PropertyGroup):
    hide_player_model: BoolProperty(
        name="Hide player model",
        default=True,
        options=set(),
    )

    hdri_face_size: IntProperty(
        name="HDRI face size",
        default=1024,
        min=10,
        options=set(),
    )

    animation_chunk_size: IntProperty(
        name="Animation chunk size",
        description="How much animation data addon will send to Outer Wilds at a time",
        default=50,
        min=1,
        options=set(),
    )

    render_timer_delay: FloatProperty(
        name="Render timer delay",
        description="Addon will send animation data and check recording progress with this timer delay (in seconds)",
        default=0.1,
        min=0.001,
        options=set(),
    )

    is_rendering: BoolProperty(
        default=False,
        options=set(),
    )

    render_stage_description: StringProperty(
        options=set(),
    )

    render_stage_progress: FloatProperty(
        default=0,
        min=0,
        max=1,
        options=set(),
    )

    @staticmethod
    def from_context(context: Context) -> "OWRecorderRenderProperties":
        return context.scene.ow_recorder_render_props
