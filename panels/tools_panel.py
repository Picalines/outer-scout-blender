import bpy
from bpy.types import Context, Panel, SpaceView3D

from ..bpy_register import bpy_register
from ..operators import WarpPlayerOperator
from ..properties import SceneProperties


@bpy_register
class ToolsPanel(Panel):
    bl_idname = "VIEW3D_PT_outer_scout_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Outer Scout"
    bl_label = "Tools"
    bl_order = 0

    @classmethod
    def poll(cls, context) -> bool:
        return SceneProperties.from_context(context).is_scene_created

    def draw(self, context):
        self._draw_sync(context)

        layout = self.layout
        warp_row = layout.row()
        warp_row.operator_context = "EXEC_DEFAULT"

        warp_props = warp_row.operator(
            operator=WarpPlayerOperator.bl_idname, text="Warp to Cursor", icon="ARMATURE_DATA"
        )

        warp_props.destination = "CURSOR"

    def _draw_sync(self, context: Context):
        return  # TODO: implement synchronize operator

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

