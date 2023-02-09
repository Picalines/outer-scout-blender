from bpy.types import Panel

from ..bpy_register import bpy_register
from ..operators.load_ground_body import OW_RECORDER_OT_load_ground_body, get_current_ground_body


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
