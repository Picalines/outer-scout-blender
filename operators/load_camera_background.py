from os import path

import bpy
from bpy.types import Camera, CameraBackgroundImage, Operator

from ..bpy_register import bpy_register
from ..properties import OWRecorderReferenceProperties
from ..utils import get_camera_color_footage_path


@bpy_register
class OW_RECORDER_OT_load_camera_background(Operator):
    """Adds or edits camera background with footage recorded in Outer Wilds"""

    bl_idname = "ow_recorder.load_camera_background"
    bl_label = "Load camera background"

    @classmethod
    def poll(cls, context) -> bool:
        return context.scene.camera is not None

    def execute(self, context):
        scene = context.scene

        color_footage_path = get_camera_color_footage_path(context, 0)
        if not path.isfile(color_footage_path):
            self.report({"ERROR"}, "recorded color footage not found")
            return {"CANCELLED"}

        reference_props = OWRecorderReferenceProperties.from_context(context)
        color_movie_clip = reference_props.main_color_movie_clip

        camera_data: Camera = scene.camera.data
        camera_data.show_background_images = True

        camera_background: CameraBackgroundImage | None = next(
            (bg for bg in camera_data.background_images if bg.clip == color_movie_clip),
            None,
        )

        if camera_background is None:
            camera_background = camera_data.background_images.new()

        if color_movie_clip is not None:
            camera_background.clip = None
            bpy.data.movieclips.remove(color_movie_clip, do_unlink=True)

        color_movie_clip = bpy.data.movieclips.load(color_footage_path)
        color_movie_clip.name = f"Outer Wilds {scene.name} free camera"
        color_movie_clip.frame_start = scene.frame_start
        reference_props.main_color_movie_clip = color_movie_clip

        camera_background.source = "MOVIE_CLIP"
        camera_background.clip = color_movie_clip
        camera_background.alpha = 1

        return {"FINISHED"}

