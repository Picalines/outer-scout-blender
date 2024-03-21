from bpy.types import Panel

from ..bpy_register import bpy_register
from ..operators import ImportBodyOperator, SetSceneOriginOperator, WarpPlayerOperator
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

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = True

        origin_row = layout.row()

        set_origin_column = origin_row.column()
        set_origin_props = set_origin_column.operator(
            SetSceneOriginOperator.bl_idname,
            text=("Set Origin" if has_origin else "Create Scene"),
            icon=("OBJECT_ORIGIN" if has_origin else "WORLD"),
        )

        if has_origin:
            set_origin_props.detect_origin_parent = False
            set_origin_props.origin_parent = scene_props.origin_parent

            warp_column = origin_row.column()
            warp_column.operator_context = "EXEC_DEFAULT"

            warp_props = warp_column.operator(
                operator=WarpPlayerOperator.bl_idname, text="Warp To Origin", icon="ARMATURE_DATA"
            )

            warp_props.destination = "ORIGIN"

        has_ground_body = scene_props.has_ground_body

        if has_origin and not has_ground_body:
            import_body_row = layout.row()
            import_body_row.operator_context = "INVOKE_DEFAULT"

            import_body_row.operator(
                ImportBodyOperator.bl_idname, text=f"Import {scene_props.origin_parent}", icon="WORLD"
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

