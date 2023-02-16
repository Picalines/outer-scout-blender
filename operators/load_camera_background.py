from os import path

import bpy
from bpy.types import Operator, Camera
from bpy.path import abspath as bpy_abspath

from ..bpy_register import bpy_register


BACKGROUND_MOVIE_CLIP_NAME = "Outer Wilds free camera"


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

        if BACKGROUND_MOVIE_CLIP_NAME in bpy.data.movieclips:
            bpy.data.movieclips.remove(
                bpy.data.movieclips[BACKGROUND_MOVIE_CLIP_NAME], do_unlink=True
            )

        background_movie_clip = bpy.data.movieclips.load(background_video_path)
        background_movie_clip.name = BACKGROUND_MOVIE_CLIP_NAME
        background_movie_clip.frame_start = context.scene.frame_start - 1

        camera_data: Camera = context.scene.camera.data

        camera_data.show_background_images = True

        camera_background = (
            camera_data.background_images.new()
            if len(camera_data.background_images) == 0
            else camera_data.background_images[0]
        )

        camera_background.source = "MOVIE_CLIP"
        camera_background.clip = background_movie_clip
        camera_background.alpha = 1

        return {"FINISHED"}
