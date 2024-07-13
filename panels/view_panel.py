import bpy
from bpy.types import Panel

from ..bpy_register import bpy_register
from ..operators import AlignGroundBodyOperator, ToggleGroundBodyOperator, WarpPlayerOperator
from ..properties import SceneProperties


@bpy_register
class ViewPanel(Panel):
    bl_idname = "VIEW3D_PT_outer_scout_view"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"
    bl_label = "Outer Scout"

    @classmethod
    def poll(cls, context) -> bool:
        return SceneProperties.from_context(context).is_scene_created

    def draw(self, context):
        layout = self.layout
        scene_props = SceneProperties.from_context(context)
        has_ground_body = scene_props.has_ground_body

        if has_ground_body:
            ground_body_visible = has_ground_body and not scene_props.ground_body.hide_get()

            show_body_props = layout.operator(
                operator=ToggleGroundBodyOperator.bl_idname,
                text=("Hide " if ground_body_visible else "Show ") + scene_props.ground_body.name,
                icon="HIDE_" + ("OFF" if ground_body_visible else "ON"),
            )

            show_body_props.action = "TOGGLE"

        warp_row = layout.row()
        warp_row.operator_context = "EXEC_DEFAULT"
        warp_props = warp_row.operator(WarpPlayerOperator.bl_idname, text="Warp to Cursor", icon="ARMATURE_DATA")
        warp_props.destination = "CURSOR"

        align_body_row = layout.row()
        align_body_row.operator_context = "EXEC_DEFAULT"
        align_body_props = align_body_row.operator(
            AlignGroundBodyOperator.bl_idname, text="Align ground to Cursor", icon="WORLD"
        )
        align_body_props.target_origin = "CURSOR"

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
