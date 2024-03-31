from bpy.props import EnumProperty
from bpy.types import Object, Operator
from mathutils import Matrix

from ..api import Transform
from ..bpy_register import bpy_register
from ..properties.scene_props import SceneProperties
from ..utils import operator_do


@bpy_register
class AlignGroundBodyOperator(Operator):
    """Align Outer Scout ground body to the scene origin"""

    bl_idname = "outer_scout.align_ground_body"
    bl_label = "Align Ground Body"

    target_origin: EnumProperty(
        name="Target Origin",
        default="SCENE_ORIGIN",
        items=[
            ("SCENE_ORIGIN", "Scene", ""),
            ("CURSOR", "Cursor", ""),
        ],
    )

    @classmethod
    def poll(cls, context) -> bool:
        scene_props = SceneProperties.from_context(context)
        return scene_props.has_origin and scene_props.has_ground_body

    @operator_do
    def execute(self, context):
        scene_props = SceneProperties.from_context(context)
        ground_body: Object = scene_props.ground_body

        match self.target_origin:
            case "SCENE_ORIGIN":
                ground_body.matrix_world = Transform.from_matrix(scene_props.origin_matrix).to_right_matrix().inverted()
            case "CURSOR":
                cursor = context.scene.cursor
                ground_body.matrix_world = cursor.matrix.inverted() @ ground_body.matrix_world
                cursor.matrix = Matrix.Identity(4)

