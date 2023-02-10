from bpy.types import Panel

from ..bpy_register import bpy_register
from ..operators.load_ground_body import OW_RECORDER_OT_load_ground_body, get_current_ground_body
from ..operators.set_ground_body_visible import OW_RECORDER_OT_set_ground_body_visible
from ..operators.move_ground_to_origin import OW_RECORDER_OT_move_ground_to_origin


@bpy_register
class OW_RECORDER_PT_ground_body(Panel):
    bl_idname = 'OW_RECORDER_PT_ground_body'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Outer Wilds Recorder'
    bl_label = 'Ground Body'

    def draw(self, _):
        current_ground_body = get_current_ground_body()
        has_ground_body = current_ground_body is not None

        self.layout.operator(
            operator=OW_RECORDER_OT_load_ground_body.bl_idname,
            icon='WORLD',
            text=('Load ground body'
                  if not has_ground_body
                  else 'Add current sector'),
        )

        self.layout.operator(
            operator=OW_RECORDER_OT_move_ground_to_origin.bl_idname,
            icon='OBJECT_ORIGIN',
        )

        ground_body_visible = has_ground_body and not current_ground_body.hide_get()

        show_body_props = self.layout.operator(
            operator=OW_RECORDER_OT_set_ground_body_visible.bl_idname,
            text=('Hide ground body'
                  if ground_body_visible
                  else 'Show ground body'),
            depress=ground_body_visible,
            icon='HIDE_' + ('OFF' if ground_body_visible else 'ON')
        )

        show_body_props.visible = not ground_body_visible
