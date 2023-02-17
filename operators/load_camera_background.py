from os import path

import bpy
from bpy.types import Operator, Camera, CameraBackgroundImage
from bpy.path import abspath as bpy_abspath

from ..bpy_register import bpy_register


@bpy_register
class OW_RECORDER_OT_load_camera_background(Operator):
    """Adds or edits camera background to rendered Outer Wilds footage"""

    bl_idname = "ow_recorder.load_camera_background"
    bl_label = "Load camera background"

    @classmethod
    def poll(cls, context) -> bool:
        return context.scene.camera is not None

    def execute(self, context):
        background_video_path = bpy_abspath("//Outer Wilds/footage/background.mp4")
        if not path.isfile(background_video_path):
            self.report({"ERROR"}, "rendered background footage not found")
            return {"CANCELLED"}

        camera_data: Camera = context.scene.camera.data

        camera_data.show_background_images = True

        camera_background: CameraBackgroundImage | None = next(
            (
                bg
                for bg in camera_data.background_images
                if bg.clip is not None and bg.clip.name.startswith("Outer Wilds")
            ),
            None,
        )

        if camera_background is None:
            camera_background = camera_data.background_images.new()

        if camera_background.clip is not None:
            background_movie_clip = camera_background.clip
            camera_background.clip = None
            bpy.data.movieclips.remove(background_movie_clip, do_unlink=True)

        background_movie_clip = bpy.data.movieclips.load(background_video_path)
        background_movie_clip.name = "Outer Wilds free camera"
        background_movie_clip.frame_start = context.scene.frame_start

        camera_background.source = "MOVIE_CLIP"
        camera_background.clip = background_movie_clip
        camera_background.alpha = 1

        return {"FINISHED"}
