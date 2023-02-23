import bpy
from bpy.types import Panel, SpaceView3D

from ..bpy_register import bpy_register
from ..operators import OW_RECORDER_OT_synchronize


@bpy_register
class OW_RECORDER_PT_synchronize(Panel):
    bl_idname = "OW_RECORDER_PT_synchronize"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Outer Wilds Recorder"
    bl_label = "Synchronize"

    def draw(self, context):
        space: SpaceView3D = context.space_data

        active_object = bpy.context.active_object
        has_active_object = active_object is not None
        is_camera_active = has_active_object and active_object.type == "CAMERA"
        is_in_camera_view = (
            context.scene.camera and space.region_3d.view_perspective == "CAMERA"
        )

        if is_in_camera_view:
            operator_text = "Sync with free camera"
        elif has_active_object:
            operator_text = "Sync with player " + (
                "camera" if is_camera_active else "body"
            )
        else:
            operator_text = "Sync with Outer Wilds"

        sync_props = self.layout.operator(
            operator=OW_RECORDER_OT_synchronize.bl_idname,
            icon="UV_SYNC_SELECT",
            text=operator_text,
        )

        if is_in_camera_view:
            sync_props.ow_item = "free_camera"
        elif has_active_object:
            sync_props.ow_item = "player/camera" if is_camera_active else "player/body"
