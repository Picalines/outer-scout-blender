import bpy
from bpy.types import Operator

from ..bpy_register import bpy_register
from ..ow_objects import get_current_ground_body


@bpy_register
class OW_RECORDER_OT_move_ground_to_origin(Operator):
    """Moves ground body so that the cursor will be in the world origin"""

    bl_idname = "ow_recorder.move_ground_to_origin"
    bl_label = "Move ground to origin"

    @classmethod
    def poll(cls, _) -> bool:
        return get_current_ground_body() is not None

    def execute(self, context):
        ground_body = get_current_ground_body()
        cursor = context.scene.cursor

        ground_body.matrix_world = (
            ground_body.matrix_world.inverted() @ cursor.matrix
        ).inverted()
        bpy.ops.view3d.snap_cursor_to_center()

        return {"FINISHED"}
