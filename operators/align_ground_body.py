from math import radians

from bpy.types import Operator
from mathutils import Matrix, Quaternion, Vector

from ..api import unity_matrix_to_blender
from ..bpy_register import bpy_register
from ..properties.scene_props import SceneProperties


@bpy_register
class AlignGroundBodyOperator(Operator):
    """Align Outer Scout ground body to the scene origin"""

    bl_idname = "outer_scout.align_ground_body"
    bl_label = "Align Ground Body"

    @classmethod
    def poll(cls, context) -> bool:
        scene_props = SceneProperties.from_context(context)
        return scene_props.has_origin and scene_props.has_ground_body

    def execute(self, context):
        scene_props = SceneProperties.from_context(context)
        ground_body = scene_props.ground_body

        origin_matrix = unity_matrix_to_blender(
            Matrix.LocRotScale(Vector(scene_props.origin_position), Quaternion(scene_props.origin_rotation), None)
        )

        ground_body.matrix_world = Matrix.Rotation(radians(90), 4, (1, 0, 0)) @ origin_matrix.inverted()

        return {"FINISHED"}

