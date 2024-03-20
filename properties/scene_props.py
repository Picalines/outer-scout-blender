from bpy.props import BoolProperty, FloatProperty, FloatVectorProperty, PointerProperty, StringProperty
from bpy.types import Context, NodeTree, PropertyGroup, Scene, Image

from ..bpy_register import bpy_register_property


@bpy_register_property(Scene, "outer_scout_scene")
class SceneProperties(PropertyGroup):
    origin_parent: StringProperty(
        name="Scene Origin Parent",
        description="Outer Wilds GameObject that the origin is attached to",
        default="",
        options=set(),
    )

    origin_position: FloatVectorProperty(
        name="Origin Position", description="Position of the scene origin", size=3, default=(0, 0, 0), options=set()
    )

    origin_rotation: FloatVectorProperty(
        name="Origin Rotation", description="Rotation of the scene origin", size=4, default=(0, 0, 0, 1), options=set()
    )

    time_scale: FloatProperty(
        name="Time scale",
        description="Use this to animate the Time.timeScale in Outer Wilds",
        default=1,
        min=0,
        options={"ANIMATABLE"},
    )

    hide_player_model: BoolProperty(
        name="Hide player model",
        default=True,
        options=set(),
    )

    hdri_node_group: PointerProperty(
        name="HDRI Node Group",
        type=NodeTree,
        options=set(),
    )

    compositor_node_group: PointerProperty(
        name="Compositor Background & Depth Node Group",
        type=NodeTree,
        options=set(),
    )

    hdri_image: PointerProperty(
        name="HDRI Image",
        type=Image,
        options=set(),
    )

    @staticmethod
    def from_context(context: Context) -> "SceneProperties":
        return context.scene.outer_scout_scene

