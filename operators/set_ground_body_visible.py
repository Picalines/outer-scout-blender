from bpy.types import Operator
from bpy.props import BoolProperty

from ..bpy_register import bpy_register
from ..ow_objects import get_current_ground_body


@bpy_register
class OW_RECORDER_OT_set_ground_body_visible(Operator):
    '''Sets ground body viewport visibility'''

    bl_idname = 'ow_recorder.set_ground_body_visible'
    bl_label = 'Toggle ground body'

    visible: BoolProperty(
        name='Visible',
        default=True,
    )

    @classmethod
    def poll(cls, _) -> bool:
        return get_current_ground_body() is not None

    def execute(self, _):
        ground_body = get_current_ground_body()

        hide = not self.visible

        ground_body.hide_set(state=hide)
        for child in ground_body.children:
            child.hide_set(state=hide)

        return {'FINISHED'}
