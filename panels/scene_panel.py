from bpy.types import Panel

from ..bpy_register import bpy_register
from ..operators import AlignGroundBodyOperator, ImportBodyOperator, SetSceneOriginOperator, WarpPlayerOperator
from ..properties import SceneProperties


@bpy_register
class ScenePanel(Panel):
    bl_idname = "DATA_PT_outer_scout_scene"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Outer Scout"
    bl_context = "scene"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene_props = SceneProperties.from_context(context)
        is_scene_created = scene_props.is_scene_created
        has_origin = scene_props.has_origin
        has_ground_body = scene_props.has_ground_body

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = True

        origin_row = layout.row()

        set_origin_column = origin_row.column()
        set_origin_props = set_origin_column.operator(
            SetSceneOriginOperator.bl_idname,
            text=("Set Origin" if has_origin else "Create Scene"),
            icon=("ORIENTATION_LOCAL" if has_origin else "WORLD"),
        )

        if has_origin:
            set_origin_props.detect_origin_parent = False
            set_origin_props.origin_parent = scene_props.origin_parent

            align_body_column = origin_row.column()
            align_body_column.operator_context = "EXEC_DEFAULT"
            align_props = align_body_column.operator(
                AlignGroundBodyOperator.bl_idname, text="Align ground to origin", icon="OBJECT_ORIGIN"
            )
            align_props.target_origin = "SCENE_ORIGIN"

            warp_row = layout.row()
            warp_row.operator_context = "EXEC_DEFAULT"

            warp_props = warp_row.operator(
                operator=WarpPlayerOperator.bl_idname, text="Warp To Origin", icon="ARMATURE_DATA"
            )
            warp_props.destination = "ORIGIN"

            import_body_row = layout.row()
            import_body_row.operator_context = "INVOKE_DEFAULT"

            import_body_row.operator(
                ImportBodyOperator.bl_idname,
                text=(
                    f"Add {scene_props.origin_parent} sectors"
                    if has_ground_body
                    else f"Import {scene_props.origin_parent}"
                ),
                icon="WORLD",
            )

        if is_scene_created:
            animation_header, anim_panel = layout.panel(f"{self.bl_idname}.animation", default_closed=False)
            animation_header.label(text="Animation")
            if anim_panel:
                anim_panel.prop(scene_props, "time_scale")

        if has_origin:
            transform_header, transform_panel = layout.panel(f"{self.bl_idname}.origin", default_closed=True)
            transform_header.label(text="Origin Transform")
            if transform_panel:
                transform_column = transform_panel.column()
                transform_column.enabled = False
                transform_column.prop(scene_props, "origin_parent")
                transform_column.prop(scene_props, "origin_position")
                transform_column.prop(scene_props, "origin_rotation")

