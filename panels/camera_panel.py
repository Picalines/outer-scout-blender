from bpy.types import Camera, Panel

from ..bpy_register import bpy_register
from ..operators import GenerateHDRINodesOperator, ImportCameraRecordingOperator
from ..properties import CameraProperties, RenderTextureProperties, SceneProperties


@bpy_register
class CameraPanel(Panel):
    bl_idname = "DATA_PT_outer_scout_camera"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Outer Scout"
    bl_context = "data"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context) -> bool:
        return (
            context.active_object.data
            and context.active_object.data.id_type == "CAMERA"
            and SceneProperties.from_context(context).is_scene_created
        )

    def draw(self, context):
        layout = self.layout

        camera: Camera = context.active_object.data
        camera_props = CameraProperties.of_camera(camera)

        layout.use_property_split = True

        layout.prop(camera_props, "outer_scout_type")

        if camera_props.outer_scout_type == "NONE":
            return

        layout.prop(camera_props, "is_recording_enabled")
        if camera_props.outer_scout_type == "EQUIRECTANGULAR":
            layout.prop(camera_props, "equirect_face_size", text="Face Size")

        self._draw_texture_panel(camera_props.color_texture_props, label="Color", id="color", default_closed=False)

        if camera_props.outer_scout_type != "EQUIRECTANGULAR":
            self._draw_texture_panel(camera_props.depth_texture_props, label="Depth", id="depth", default_closed=True)
        else:
            hdri_header, hdri_panel = layout.panel(f"{self.__class__.__name__}.hdri", default_closed=True)
            hdri_header.label(text="HDRI")

            if hdri_panel:
                hdri_panel.enabled = False
                hdri_panel.prop(camera_props, "hdri_image")
                hdri_panel.prop(camera_props, "hdri_node_group")

        import_bg_row = layout.row()
        import_bg_row.operator(ImportCameraRecordingOperator.bl_idname, icon="FILE_MOVIE")

        if camera_props.outer_scout_type == "EQUIRECTANGULAR":
            hdri_row = layout.row()
            hdri_row.operator(GenerateHDRINodesOperator.bl_idname, icon="NODE_MATERIAL")

    def _draw_texture_panel(
        self, ffmpeg_options: RenderTextureProperties, *, label: str, id: str, default_closed: bool
    ):
        layout = self.layout

        texture_header, texture_panel = layout.panel(f"{self.__class__.__name__}.{id}", default_closed=default_closed)
        texture_header.label(text=label)

        if texture_panel:
            texture_panel.prop(ffmpeg_options, "recording_path")
            texture_panel.prop(ffmpeg_options, "constant_rate_factor")

            footage_column = texture_panel.column()
            footage_column.enabled = False
            footage_column.prop(ffmpeg_options, "movie_clip")

