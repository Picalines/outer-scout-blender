from bpy.types import Panel

from ..bpy_register import bpy_register
from ..operators import (
    AlignGroundBodyOperator,
    GenerateCompositorNodesOperator,
    ImportAssetsOperator,
    ImportBodyOperator,
    RecordOperator,
    SetSceneOriginOperator,
    WarpPlayerOperator,
)
from ..properties import SceneProperties, SceneRecordingProperties


@bpy_register
class ScenePanel(Panel):
    bl_idname = "DATA_PT_outer_scout_scene"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Outer Scout"
    bl_context = "scene"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene = context.scene
        scene_props = SceneProperties.from_context(context)
        recording_props = SceneRecordingProperties.from_context(context)

        layout = self.layout
        layout.enabled = not recording_props.in_progress
        layout.use_property_split = True
        layout.use_property_decorate = True

        if not scene_props.is_scene_created or not scene_props.has_origin:
            origin_row = layout.row()
            set_origin_column = origin_row.column()
            set_origin_column.operator(SetSceneOriginOperator.bl_idname, text="Create Scene", icon="WORLD")
            return

        animation_header, anim_panel = layout.panel(f"{self.bl_idname}.animation", default_closed=False)
        animation_header.label(text="Animation", icon="GRAPH")
        if anim_panel:
            anim_panel.prop(scene_props, "time_scale")

        origin_header, origin_panel = layout.panel(f"{self.bl_idname}.origin", default_closed=False)
        origin_header.label(text="Origin", icon="ORIENTATION_VIEW")
        if origin_panel:
            origin_row = origin_panel.row()

            set_origin_column = origin_row.column()
            set_origin_column.operator_context = "INVOKE_DEFAULT"
            set_origin_props = set_origin_column.operator(SetSceneOriginOperator.bl_idname, icon="WORLD")
            set_origin_props.detect_origin_parent = False
            set_origin_props.origin_parent = scene_props.origin_parent

            align_body_column = origin_row.column()
            align_body_column.operator_context = "EXEC_DEFAULT"
            align_props = align_body_column.operator(
                AlignGroundBodyOperator.bl_idname, text="Align ground to origin", icon="OBJECT_ORIGIN"
            )
            align_props.target_origin = "SCENE_ORIGIN"

            warp_row = origin_panel.row()
            warp_row.operator_context = "EXEC_DEFAULT"
            warp_props = warp_row.operator(
                operator=WarpPlayerOperator.bl_idname, text="Warp To Origin", icon="ARMATURE_DATA"
            )
            warp_props.destination = "ORIGIN"

            transform_header, transform_panel = origin_panel.panel(
                f"{self.bl_idname}.origin.transform", default_closed=True
            )
            transform_header.label(text="Origin Transform")
            if transform_panel:
                transform_column = transform_panel.column()
                transform_column.enabled = False
                transform_column.prop(scene_props, "origin_parent")
                transform_column.prop(scene_props, "origin_position")
                transform_column.prop(scene_props, "origin_rotation")

        ground_header, ground_panel = layout.panel(f"{self.bl_idname}.ground_body", default_closed=False)
        ground_header.label(text="Ground Body", icon="WORLD")
        if ground_panel:
            ground_panel.prop(scene_props, "outer_wilds_scene")

            has_ground_body = scene_props.has_ground_body

            ground_panel.operator_context = "INVOKE_DEFAULT"
            ground_panel.operator(
                ImportBodyOperator.bl_idname,
                text=(
                    f"Add {scene_props.origin_parent} sectors"
                    if has_ground_body
                    else f"Import {scene_props.origin_parent}"
                ),
                icon=("OVERLAY" if has_ground_body else "LINKED"),
            )

        record_header, record_panel = layout.panel(f"{self.bl_idname}.record", default_closed=False)
        record_header.label(text="Record", icon="VIEW_CAMERA")
        if record_panel:
            if recording_props.in_progress:
                record_panel.progress(text="Recording...", factor=recording_props.progress, type="BAR")
            else:
                record_panel.operator_context = "INVOKE_DEFAULT"
                record_panel.operator(operator=RecordOperator.bl_idname, icon="RENDER_ANIMATION")

            rsettings_header, rsettings_panel = record_panel.panel(f"{self.bl_idname}.settings", default_closed=True)
            rsettings_header.label(text="Recording Settings")

            if rsettings_panel:
                rsettings_panel.prop(recording_props, "modal_timer_delay")

        comp_header, comp_panel = layout.panel(f"{self.bl_idname}.comp", default_closed=True)
        comp_header.label(text="Compositing", icon="NODE_COMPOSITING")
        if comp_panel:
            if not scene.render.film_transparent:
                comp_panel.label(text="Transparent rendering is not enabled", icon="ERROR")
            comp_panel.operator_context = "EXEC_DEFAULT"
            comp_panel.operator(GenerateCompositorNodesOperator.bl_idname, icon="NODE_COMPOSITING")

        assets_row = layout.row()
        assets_row.operator_context = "EXEC_DEFAULT"
        assets_row.operator(ImportAssetsOperator.bl_idname, icon="FILE_REFRESH")
