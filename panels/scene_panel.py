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

        if not scene.render.film_transparent:
            layout.box().label(text="Transparent rendering is not enabled", icon="ERROR")
            layout.separator()

        layout.prop(scene_props, "outer_wilds_scene")
        layout.prop(scene_props, "time_scale")

        layout.separator()

        layout.operator_context = "INVOKE_DEFAULT"
        has_ground_body = scene_props.has_ground_body
        layout.operator(
            ImportBodyOperator.bl_idname,
            text=(
                f"Add {scene_props.origin_parent} sectors" if has_ground_body else f"Import {scene_props.origin_parent}"
            ),
            icon=("OVERLAY" if has_ground_body else "LINKED"),
        )

        origin_row = layout.row()

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

        layout.operator_context = "EXEC_DEFAULT"
        warp_props = layout.operator(WarpPlayerOperator.bl_idname, text="Warp To Origin", icon="ARMATURE_DATA")
        warp_props.destination = "ORIGIN"

        layout.separator()

        if recording_props.in_progress:
            layout.progress(text="Recording...", factor=recording_props.progress, type="BAR")
        else:
            layout.operator_context = "INVOKE_DEFAULT"
            layout.operator(RecordOperator.bl_idname, icon="RENDER_ANIMATION")

        layout.separator()

        layout.operator_context = "EXEC_DEFAULT"
        layout.operator(ImportAssetsOperator.bl_idname, icon="FILE_REFRESH")

        layout.operator_context = "EXEC_DEFAULT"
        layout.operator(GenerateCompositorNodesOperator.bl_idname, icon="NODE_COMPOSITING")

        layout.separator()

        transform_header, transform_panel = layout.panel(f"{self.bl_idname}.origin.transform", default_closed=True)
        transform_header.label(text="Origin Transform")
        if transform_panel:
            transform_column = transform_panel.column()
            transform_column.enabled = False
            transform_column.prop(scene_props, "origin_parent")
            transform_column.prop(scene_props, "origin_position")
            transform_column.prop(scene_props, "origin_rotation")
