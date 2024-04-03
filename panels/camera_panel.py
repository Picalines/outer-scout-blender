from bpy.types import Camera, Panel

from ..bpy_register import bpy_register
from ..operators import GenerateHDRINodesOperator, ImportCameraRecordingOperator
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

        import_bg_row = layout.row()
        import_bg_row.operator(ImportCameraRecordingOperator.bl_idname, icon="FILE_MOVIE")

        if camera_props.outer_scout_type == "EQUIRECTANGULAR":
            hdri_row = layout.row()
            hdri_row.operator(GenerateHDRINodesOperator.bl_idname, icon="NODE_MATERIAL")

        footage_header, footage_panel = layout.panel(f"{self.__class__.__name__}.clips", default_closed=True)
        footage_header.label(text="Imported Footage")
        if footage_panel:
            footage_panel.enabled = False
            footage_panel.prop(camera_props, "color_movie_clip")
            footage_panel.prop(camera_props, "depth_movie_clip")
            footage_panel.prop(camera_props, "hdri_image")

