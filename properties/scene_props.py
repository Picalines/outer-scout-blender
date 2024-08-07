from bpy.props import BoolProperty, FloatProperty, FloatVectorProperty, PointerProperty, StringProperty
from bpy.types import Context, NodeTree, Object, PropertyGroup, Scene
from mathutils import Matrix, Quaternion, Vector

from ..bpy_register import bpy_register_property


@bpy_register_property(Scene, "outer_scout_scene")
class SceneProperties(PropertyGroup):
    outer_wilds_scene: StringProperty(
        name="Outer Wilds Scene",
        description="Name of the Outer Wilds scene. It's used for safety checks, clear to ignore",
        default="",
        options=set(),
    )

    origin_parent: StringProperty(
        name="Scene Origin Parent",
        description="Outer Wilds GameObject that the origin is attached to",
        default="",
        options=set(),
    )

    origin_position: FloatVectorProperty(
        name="Origin Position",
        description="Position of the scene origin (in Unity coordinate system)",
        subtype="XYZ",
        size=3,
        default=(0, 0, 0),
        options=set(),
    )

    origin_rotation: FloatVectorProperty(
        name="Origin Rotation",
        description="Rotation of the scene origin (in Unity coordinate system)",
        subtype="QUATERNION",
        size=4,
        default=(1, 0, 0, 0),
        options=set(),
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

    ground_body: PointerProperty(name="Ground Body", type=Object, options=set())

    compositor_node_group: PointerProperty(
        name="Compositor Background & Depth Node Group",
        type=NodeTree,
        options=set(),
    )

    @staticmethod
    def from_context(context: Context) -> "SceneProperties":
        return context.scene.outer_scout_scene

    @property
    def is_scene_created(self) -> bool:
        return self.origin_parent != ""

    @property
    def has_origin(self) -> bool:
        return self.origin_parent != ""

    @property
    def has_ground_body(self) -> bool:
        return self.ground_body is not None

    @property
    def origin_matrix(self) -> Matrix:
        return Matrix.LocRotScale(Vector(self.origin_position), Quaternion(self.origin_rotation), None)
