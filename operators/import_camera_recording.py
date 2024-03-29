import bpy
from bpy.path import abspath
from bpy.types import Camera, CameraBackgroundImage, Object, Operator

from ..bpy_register import bpy_register
from ..properties import CameraProperties, SceneProperties
from ..utils import operator_do


@bpy_register
class ImportCameraRecordingOperator(Operator):
    """Adds or edits camera background with footage recorded in Outer Wilds"""

    bl_idname = "outer_scout.import_camera_recording"
    bl_label = "Import Recordings"

    @classmethod
    def poll(cls, context) -> bool:
        scene_props = SceneProperties.from_context(context)
        if not scene_props.is_scene_created:
            return False

        active_object: Object = context.active_object
        if active_object.type != "CAMERA":
            return False

        camera_props = CameraProperties.of_camera(active_object.data)
        return camera_props.has_color_recording_path or camera_props.has_depth_recording_path

    @operator_do
    def execute(self, context):
        scene = context.scene
        camera: Camera = context.active_object.data

        camera.show_background_images = True

        camera_props = CameraProperties.of_camera(camera)
        color_movie_clip = camera_props.color_movie_clip

        camera_background: CameraBackgroundImage | None = next(
            (bg for bg in camera.background_images if bg.clip == color_movie_clip), None
        )

        if color_movie_clip is not None:
            bpy.data.movieclips.remove(color_movie_clip, do_unlink=True)

        if camera_props.has_color_recording_path:
            color_movie_clip = bpy.data.movieclips.load(abspath(camera_props.color_recording_path))
            camera_props.color_movie_clip = color_movie_clip

            color_movie_clip.name = f"OW.{camera.name}.color"
            color_movie_clip.frame_start = scene.frame_start

            if camera_props.outer_scout_type == "PERSPECTIVE":

                if camera_background is None:
                    camera_background = camera.background_images.new()
                    camera_background.alpha = 1

                camera_background.source = "MOVIE_CLIP"
                camera_background.clip = color_movie_clip

        depth_movie_clip = camera_props.depth_movie_clip
        if depth_movie_clip is not None:
            bpy.data.movieclips.remove(depth_movie_clip, do_unlink=True)

        if camera_props.has_depth_recording_path:
            depth_movie_clip = bpy.data.movieclips.load(abspath(camera_props.depth_recording_path))
            camera_props.depth_movie_clip = depth_movie_clip

            depth_movie_clip.name = f"OW.{camera.name}.depth"
            depth_movie_clip.frame_start = scene.frame_start

