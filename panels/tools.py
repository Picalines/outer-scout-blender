import bpy
from bpy.types import Context, Panel, SpaceView3D

from ..bpy_register import bpy_register
from ..operators import OW_RECORDER_OT_save_warp_transform, OW_RECORDER_OT_synchronize, OW_RECORDER_OT_warp
from ..properties import OWRecorderReferenceProperties


@bpy_register
class OW_RECORDER_PT_tools(Panel):
    bl_idname = "OW_RECORDER_PT_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Outer Wilds Recorder"
    bl_label = "Tools"
    bl_order = 0

    @classmethod
    def poll(cls, context) -> bool:
        reference_props = OWRecorderReferenceProperties.from_context(context)
        return bool(reference_props.ground_body)

    def draw(self, context):
        self._draw_sync(context)

        row = self.layout.row()
        row.operator(operator=OW_RECORDER_OT_warp.bl_idname, text="Warp", icon="ORIENTATION_PARENT")
        row.operator(operator=OW_RECORDER_OT_save_warp_transform.bl_idname, text="Save", icon="CURRENT_FILE")

    def _draw_sync(self, context: Context):
        space: SpaceView3D = context.space_data

        active_object = bpy.context.active_object
        has_active_object = active_object is not None
        is_camera_active = has_active_object and active_object.type == "CAMERA"
        is_in_camera_view = context.scene.camera and space.region_3d.view_perspective == "CAMERA"

        if is_in_camera_view:
            operator_text = "Sync with free camera"
        elif has_active_object:
            operator_text = "Sync with player " + ("camera" if is_camera_active else "body")
        else:
            operator_text = "Sync with Outer Wilds"

        sync_props = self.layout.operator(
            operator=OW_RECORDER_OT_synchronize.bl_idname,
            icon="UV_SYNC_SELECT",
            text=operator_text,
        )

        if is_in_camera_view:
            sync_props.ow_item = "free-camera"
        elif has_active_object:
            sync_props.ow_item = "player/camera" if is_camera_active else "player/body"

