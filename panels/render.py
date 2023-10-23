from bpy.types import Panel

from ..bpy_register import bpy_register
from ..properties import OWRecorderRenderProperties
from ..operators.render import OW_RECORDER_OT_render


@bpy_register
class OW_RECORDER_PT_render(Panel):
    bl_idname = "OW_RECORDER_PT_render"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Outer Wilds Recorder"
    bl_label = "Render"

    def draw(self, context):
        render_props = OWRecorderRenderProperties.from_context(context)

        self.layout.enabled = not render_props.is_rendering

        self.layout.prop(render_props, "hide_player_model")

        row = self.layout.row()
        row.prop(render_props, "use_background", text="Bg", toggle=1)
        row.prop(render_props, "use_hdri", text="HDRI", toggle=1)
        row.prop(render_props, "use_depth", text="Depth", toggle=1)

        if render_props.record_hdri:
            self.layout.prop(render_props, "hdri_face_size")

        if not render_props.is_rendering:
            self.layout.operator(
                operator=OW_RECORDER_OT_render.bl_idname,
                icon="RENDER_ANIMATION",
            )
        else:
            row = self.layout.row(align=True)
            row.enabled = False
            row.prop(
                data=render_props,
                property="render_stage_progress",
                text=render_props.render_stage_description,
                slider=True,
            )


@bpy_register
class OW_RECORDER_PT_render_editor_settings(Panel):
    bl_idname = "OW_RECORDER_PT_render_editor_settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Outer Wilds Recorder"
    bl_parent_id = "OW_RECORDER_PT_render"
    bl_label = "Editor settings"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        render_props = OWRecorderRenderProperties.from_context(context)
        self.layout.enabled = not render_props.is_rendering

        self.layout.prop(render_props, "show_progress_gui")
        self.layout.prop(render_props, "animation_chunk_size")
        self.layout.prop(render_props, "render_timer_delay")
