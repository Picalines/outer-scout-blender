from math import radians

from bpy.types import Operator
from mathutils import Matrix

from ..api import unity_quaternion_to_blender, unity_vector_to_blender
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

        origin_matrix = (
            Matrix.Translation(unity_vector_to_blender(scene_props.origin_position))
            @ unity_quaternion_to_blender(scene_props.origin_rotation).to_matrix().to_4x4()
        )

        ground_body.matrix_world = Matrix.Rotation(radians(90), 4, (1, 0, 0)) @ origin_matrix.inverted()

        return {"FINISHED"}

