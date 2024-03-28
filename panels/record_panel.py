from bpy.types import Panel

from ..bpy_register import bpy_register
from ..operators import RecordOperator
from ..properties import RecordingProperties, SceneProperties


@bpy_register
class OW_RECORDER_PT_recorder(Panel):
    bl_idname = "DATA_PT_outer_scout_record"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_label = "Outer Scout"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context) -> bool:
        scene_props = SceneProperties.from_context(context)
        return scene_props.is_scene_created and scene_props.has_origin

    def draw(self, context):
        layout = self.layout
        recording_props = RecordingProperties.from_context(context)

        layout.use_property_split = True
        layout.enabled = not recording_props.in_progress

        if recording_props.in_progress:
            layout.progress(text="Recording...", factor=recording_props.progress, type="BAR")
        else:
            layout.operator(operator=RecordOperator.bl_idname, icon="RENDER_ANIMATION")

        settings_header, settings_panel = layout.panel(f"{self.__class__.__name__}.settings", default_closed=True)
        settings_header.label(text="Editor Settings")

        if settings_panel:
            settings_panel.prop(recording_props, "animation_chunk_size")
            settings_panel.prop(recording_props, "modal_timer_delay")

