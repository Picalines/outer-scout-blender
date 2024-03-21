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

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = True

        has_origin = scene_props.has_origin

        if has_origin:
            header, panel = layout.panel(f"{self.bl_idname}.origin", default_closed=True)
            header.label(text=f"Origin: {scene_props.origin_parent}")
            if panel:
                column = layout.column()
                column.enabled = False
                column.prop(scene_props, "origin_parent")
                column.prop(scene_props, "origin_position")
                column.prop(scene_props, "origin_rotation")

        set_origin_props = layout.operator(
            SetSceneOriginOperator.bl_idname,
            text=("Set Origin" if has_origin else "Create Scene"),
            icon=("OBJECT_ORIGIN" if has_origin else "WORLD"),
        )

        if has_origin:
            set_origin_props.detect_origin_parent = False
            set_origin_props.origin_parent = scene_props.origin_parent

            warp_row = layout.row()
            warp_row.operator_context = "EXEC_DEFAULT"

            warp_props = warp_row.operator(
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

