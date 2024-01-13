from bpy.types import Context, Scene, PropertyGroup, Object, MovieClip, Image, NodeTree
from bpy.props import PointerProperty

from ..bpy_register import bpy_register_property


@bpy_register_property(Scene, "ow_recorder_reference_props")
class OWRecorderReferenceProperties(PropertyGroup):
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

    main_color_movie_clip: PointerProperty(
        name="Color Movie Clip",
        type=MovieClip,
        options=set(),
    )

    main_depth_movie_clip: PointerProperty(
        name="Depth Movie Clip",
        type=MovieClip,
        options=set(),
    )

    hdri_image: PointerProperty(
        name="HDRI Image",
        type=Image,
        options=set(),
    )

    hdri_node_tree: PointerProperty(
        name="HDRI Node Group",
        type=NodeTree,
        options=set(),
    )

    compositor_node_tree: PointerProperty(
        name="Compositor Background & Depth Node Group",
        type=NodeTree,
        options=set(),
    )

    @staticmethod
    def from_context(context: Context) -> "OWRecorderReferenceProperties":
        return context.scene.ow_recorder_reference_props
