from bpy.types import Camera, Panel

from ..bpy_register import bpy_register
from ..properties import CameraProperties, SceneProperties


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

        match camera_props.outer_scout_type:
            case "PERSPECTIVE":
                layout.prop(camera_props, "color_recording_path")
                layout.prop(camera_props, "depth_recording_path")
            case "EQUIRECTANGULAR":
                layout.prop(camera_props, "color_recording_path", text="Recording Path")
                layout.prop(camera_props, "equirect_face_size", text="Face Size")

        clip_header, clip_panel = layout.panel(f"{self.__class__.__name__}.clips", default_closed=True)
        clip_header.label(text="Movie Clips")
        if clip_panel:
            clip_panel.enabled = False
            clip_panel.prop(camera_props, "color_movie_clip")
            clip_panel.prop(camera_props, "depth_movie_clip")

