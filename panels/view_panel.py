import bpy
from bpy.types import Context, Panel

from ..bpy_register import bpy_extend_panel
from ..operators import WarpPlayerOperator
from ..properties import SceneProperties


@bpy_extend_panel(bpy.types.VIEW3D_PT_view3d_cursor)
def draw_view_panel(panel: Panel, context: Context):
    scene_props = SceneProperties.from_context(context)
    if not scene_props.is_scene_created:
        return

    layout = panel.layout
    header, panel = layout.panel(f"{__package__}.{draw_view_panel.__name__}", default_closed=False)
    header.label(text="Outer Scout")
    if not panel:
        return

    warp_row = panel.row()
    warp_row.operator_context = "EXEC_DEFAULT"
    warp_props = warp_row.operator(operator=WarpPlayerOperator.bl_idname, text="Warp to Cursor", icon="ARMATURE_DATA")
    warp_props.destination = "CURSOR"

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


