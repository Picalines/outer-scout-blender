from bpy.types import Context, Scene, PropertyGroup, Object, MovieClip, Image
from bpy.props import PointerProperty

from ..bpy_register import bpy_register_property


@bpy_register_property(Scene, "ow_recorder_reference_props")
class OWRecorderReferencePropertis(PropertyGroup):
    ground_body: PointerProperty(
        name="Ground Body",
        type=Object,
        options=set(),
    )

    hdri_pivot: PointerProperty(
        name="HDRI Pivot",
        type=Object,
        options=set(),
    )

    background_movie_clip: PointerProperty(
        name="Background Movie Clip",
        type=MovieClip,
        options=set(),
    )

    hdri_image: PointerProperty(
        name="HDRI Image",
        type=Image,
        options=set(),
    )

    @staticmethod
    def from_context(context: Context) -> "OWRecorderReferencePropertis":
        return context.scene.ow_recorder_reference_props
