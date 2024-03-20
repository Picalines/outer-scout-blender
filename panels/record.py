from bpy.types import Panel

from ..bpy_register import bpy_register
from ..operators import OW_RECORDER_OT_load_camera_background, OW_RECORDER_OT_record
from ..properties import RecordingProperties, OWRecorderReferenceProperties


@bpy_register
class OW_RECORDER_PT_recorder(Panel):
    bl_idname = "OW_RECORDER_PT_recorder"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Outer Wilds Recorder"
    bl_label = "Recorder"
    bl_order = 5

    @classmethod
    def poll(cls, context) -> bool:
        reference_props = OWRecorderReferenceProperties.from_context(context)
        return all(
            (
                reference_props.ground_body,
                reference_props.hdri_pivot,
            )
        )

    def draw(self, context):
        recorder_props = RecordingProperties.from_context(context)

        self.layout.enabled = not recorder_props.is_recording

        self.layout.prop(recorder_props, "hide_player_model")

        row = self.layout.row()
        row.prop(recorder_props, "record_hdri", text="HDRI", toggle=1)
        row.prop(recorder_props, "record_depth", text="Depth", toggle=1)

        if recorder_props.record_hdri:
            self.layout.prop(recorder_props, "hdri_face_size")

        if not recorder_props.is_recording:
            self.layout.operator(
                operator=OW_RECORDER_OT_record.bl_idname,
                icon="RENDER_ANIMATION",
            )
        else:
            row = self.layout.row(align=True)
            row.enabled = False
            row.prop(
                data=recorder_props,
                property="stage_progress",
                text=recorder_props.stage_description,
                slider=True,
            )

        column = self.layout.column()
        column.enabled = not recorder_props.is_recording
        column.operator(operator=OW_RECORDER_OT_load_camera_background.bl_idname, icon="CAMERA_DATA")


@bpy_register
class OW_RECORDER_PT_recorder_editor_settings(Panel):
    bl_idname = "OW_RECORDER_PT_recorder_editor_settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Outer Wilds Recorder"
    bl_parent_id = OW_RECORDER_PT_recorder.bl_idname
    bl_label = "Editor settings"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        recorder_props = RecordingProperties.from_context(context)
        self.layout.enabled = not recorder_props.is_recording

        self.layout.prop(recorder_props, "animation_chunk_size")
        self.layout.prop(recorder_props, "modal_timer_delay")

