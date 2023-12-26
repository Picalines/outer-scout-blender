import bpy
from bpy.types import Object, Operator

from ..bpy_register import bpy_register
from ..properties import OWRecorderReferenceProperties


@bpy_register
class OW_RECORDER_OT_move_ground_to_origin(Operator):
    """Moves ground body so that the cursor will be in the world origin"""

    bl_idname = "ow_recorder.move_ground_to_origin"
    bl_label = "Move ground to origin"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context) -> bool:
        reference_props = OWRecorderReferenceProperties.from_context(context)
        return reference_props.ground_body is not None

    def execute(self, context):
        reference_props = OWRecorderReferenceProperties.from_context(context)
        ground_body: Object = reference_props.ground_body
        cursor = context.scene.cursor

        ground_body.matrix_world = (ground_body.matrix_world.inverted() @ cursor.matrix).inverted()

        with context.temp_override():
            bpy.ops.view3d.snap_cursor_to_center()

        return {"FINISHED"}

