from bpy.types import Panel

from ..operators.render import OW_RECORDER_OT_render


class OW_RECORDER_PT_render(Panel):
    bl_idname = 'OW_RECORDER_PT_render'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Outer Wilds Recorder'
    bl_label = 'Render'

    def draw(self, _):
        self.layout.operator(
            operator=OW_RECORDER_OT_render.bl_idname,
            icon='RENDER_ANIMATION'
        )
