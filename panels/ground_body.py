from bpy.types import Object, Panel

from ..bpy_register import bpy_register
from ..operators.load_ground_body import OW_RECORDER_OT_load_ground_body
from ..operators.move_ground_to_origin import OW_RECORDER_OT_move_ground_to_origin
from ..operators.set_ground_body_visible import OW_RECORDER_OT_set_ground_body_visible
from ..properties import OWRecorderReferenceProperties, OWRecorderSceneProperties


@bpy_register
class OW_RECORDER_PT_ground_body(Panel):
    bl_idname = "OW_RECORDER_PT_ground_body"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Outer Wilds Recorder"
    bl_label = "Ground Body"
    bl_order = 3

    def draw(self, context):
        reference_props = OWRecorderReferenceProperties.from_context(context)
        scene_props = OWRecorderSceneProperties.from_context(context)

        current_ground_body: Object = reference_props.ground_body
        has_ground_body = current_ground_body is not None

        ground_body_text = scene_props.ground_body_name.removesuffix("_Body") or "ground body"

        load_ground_body_props = self.layout.operator(
            operator=OW_RECORDER_OT_load_ground_body.bl_idname,
            text=("Load ground body" if not has_ground_body else "Add current sector"),
            icon="WORLD",
        )

        load_ground_body_props.move_ground_to_origin = not has_ground_body

        self.layout.operator(
            operator=OW_RECORDER_OT_move_ground_to_origin.bl_idname,
            text=f"Move {ground_body_text} to origin",
            icon="OBJECT_ORIGIN",
        )

        ground_body_visible = has_ground_body and not current_ground_body.hide_get()

        show_body_props = self.layout.operator(
            operator=OW_RECORDER_OT_set_ground_body_visible.bl_idname,
            text=("Hide " if ground_body_visible else "Show ") + ground_body_text,
            depress=ground_body_visible,
            icon="HIDE_" + ("OFF" if ground_body_visible else "ON"),
        )

        show_body_props.visible = not ground_body_visible

