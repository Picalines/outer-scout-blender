from bpy.types import Panel

from ..bpy_register import bpy_register
from ..properties import OWRecorderRenderProperties
from ..operators.render import OW_RECORDER_OT_render


@bpy_register
class OW_RECORDER_PT_render(Panel):
    bl_idname = 'OW_RECORDER_PT_render'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Outer Wilds Recorder'
    bl_label = 'Render'

    def draw(self, context):
        render_props = OWRecorderRenderProperties.from_context(context)

        self.layout.enabled = not render_props.is_rendering

        self.layout.prop(render_props, 'hide_player_model')
        self.layout.prop(render_props, 'hdri_face_size')

        if not render_props.is_rendering:
            self.layout.operator(
                operator=OW_RECORDER_OT_render.bl_idname,
                icon='RENDER_ANIMATION',
            )
        else:
            row = self.layout.row(align=True)
            row.enabled = False
            row.prop(
                data=render_props,
                property='render_progress',
                text='Rendering...',
                slider=True,
            )
