from bpy.types import Operator

from ..api import Transform
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

        ground_body.matrix_world = Transform.from_matrix(scene_props.origin_matrix).to_right_matrix().inverted()

        return {"FINISHED"}

