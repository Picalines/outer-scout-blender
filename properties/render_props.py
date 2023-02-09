from bpy.types import PropertyGroup, Context, Scene
from bpy.props import BoolProperty, IntProperty, FloatProperty

from ..bpy_register import bpy_register_property


@bpy_register_property(Scene, 'ow_recorder_render_props')
class OWRecorderRenderProperties(PropertyGroup):
    hide_player_model: BoolProperty(
        name='Hide player model',
        default=True,
    )

    hdri_face_size: IntProperty(
        name='HDRI face size',
        default=1024,
        min=10,
    )

    is_rendering: BoolProperty(
        default=False
    )

    render_progress: FloatProperty(
        default=0,
        min=0,
        max=1,
    )

    @staticmethod
    def from_context(context: Context) -> 'OWRecorderRenderProperties':
        return context.scene.ow_recorder_render_props
