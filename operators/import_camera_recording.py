from os import path

import bpy
from bpy.path import abspath
from bpy.types import Camera, CameraBackgroundImage, Object, Operator

from ..bpy_register import bpy_register
from ..properties import CameraProperties
from ..utils import Result, operator_do


@bpy_register
class ImportCameraRecordingOperator(Operator):
    """Adds or edits camera background with footage recorded in Outer Wilds"""

    bl_idname = "outer_scout.import_camera_recording"
    bl_label = "Import Recordings"

    @classmethod
    def poll(cls, context) -> bool:
        active_object: Object = context.active_object
        if not active_object or active_object.type != "CAMERA":
            return False

        camera_props = CameraProperties.of_camera(active_object.data)
        return camera_props.has_color_recording_path or camera_props.has_depth_recording_path

    @operator_do
    def execute(self, context):
        scene = context.scene
        camera: Camera = context.active_object.data

        camera.show_background_images = True

        camera_props = CameraProperties.of_camera(camera)

        if camera_props.has_color_recording_path:
            color_recording_path = abspath(camera_props.color_recording_path)
            if not path.isfile(color_recording_path):
                Result.do_error(f'file "{camera_props.color_recording_path}" not found')

        if camera_props.has_depth_recording_path:
            depth_recording_path = abspath(camera_props.depth_recording_path)
            if not path.isfile(depth_recording_path):
                Result.do_error(f'file "{camera_props.depth_recording_path}" not found')

        color_movie_clip = camera_props.color_movie_clip
        camera_background: CameraBackgroundImage | None = (
            next((bg for bg in camera.background_images if bg.clip == color_movie_clip), None)
            if color_movie_clip is not None
            else None
        )

        if camera_props.has_color_recording_path:
            if color_movie_clip:
                bpy.data.movieclips.remove(color_movie_clip, do_unlink=True)

            color_movie_clip = bpy.data.movieclips.load(color_recording_path)
            camera_props.color_movie_clip = color_movie_clip

            color_movie_clip.name = f"outer_scout.{camera.name}.color"
            color_movie_clip.frame_start = scene.frame_start

            if camera_props.outer_scout_type == "PERSPECTIVE":
                if camera_background is None:
                    camera_background = camera.background_images.new()
                    camera_background.alpha = 1

                camera_background.source = "MOVIE_CLIP"
                camera_background.clip = color_movie_clip

        if camera_props.has_depth_recording_path:
            depth_movie_clip = camera_props.depth_movie_clip
            if depth_movie_clip is not None:
                bpy.data.movieclips.remove(depth_movie_clip, do_unlink=True)

            depth_movie_clip = bpy.data.movieclips.load(depth_recording_path)
            camera_props.depth_movie_clip = depth_movie_clip

            depth_movie_clip.name = f"outer_scout.{camera.name}.depth"
            depth_movie_clip.frame_start = scene.frame_start

