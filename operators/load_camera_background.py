from os import path

import bpy
from bpy.types import Operator, Camera, CameraBackgroundImage

from ..bpy_register import bpy_register
from ..utils import get_background_video_path
from ..properties import OWRecorderReferenceProperties


@bpy_register
class OW_RECORDER_OT_load_camera_background(Operator):
    """Adds or edits camera background to rendered Outer Wilds footage"""

    bl_idname = "ow_recorder.load_camera_background"
    bl_label = "Load camera background"

    @classmethod
    def poll(cls, context) -> bool:
        return context.scene.camera is not None

    def execute(self, context):
        scene = context.scene

        background_video_path = get_background_video_path(context)
        if not path.isfile(background_video_path):
            self.report({"ERROR"}, "rendered background footage not found")
            return {"CANCELLED"}

        reference_props = OWRecorderReferenceProperties.from_context(context)
        background_movie_clip = reference_props.background_movie_clip

        camera_data: Camera = scene.camera.data
        camera_data.show_background_images = True

        camera_background: CameraBackgroundImage | None = next(
            (bg for bg in camera_data.background_images if bg.clip == background_movie_clip),
            None,
        )

        if camera_background is None:
            camera_background = camera_data.background_images.new()

        if background_movie_clip is not None:
            camera_background.clip = None
            bpy.data.movieclips.remove(background_movie_clip, do_unlink=True)

        background_movie_clip = bpy.data.movieclips.load(background_video_path)
        background_movie_clip.name = f"Outer Wilds {scene.name} free camera"
        background_movie_clip.frame_start = scene.frame_start
        reference_props.background_movie_clip = background_movie_clip

        camera_background.source = "MOVIE_CLIP"
        camera_background.clip = background_movie_clip
        camera_background.alpha = 1

        return {"FINISHED"}
