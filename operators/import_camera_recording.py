from os import path

import bpy
from bpy.types import Camera, CameraBackgroundImage, MovieClip, Object, Operator, Scene

from ..bpy_register import bpy_register
from ..properties import CameraProperties, RenderTextureProperties
from ..utils import Result, operator_do


@bpy_register
class ImportCameraRecordingOperator(Operator):
    """Imports the footage recorded by the camera in Outer Wilds"""

    bl_idname = "outer_scout.import_camera_recording"
    bl_label = "Import Recordings"

    @classmethod
    def poll(cls, context) -> bool:
        active_object: Object = context.active_object
        if not active_object or active_object.type != "CAMERA":
            return False

        return CameraProperties.of_camera(active_object.data).has_any_recording_path

    @operator_do
    def execute(self, context):
        scene = context.scene
        camera: Camera = context.active_object.data

        camera.show_background_images = True

        camera_props = CameraProperties.of_camera(camera)

        color_movie_clip = camera_props.color_texture_props.movie_clip
        camera_background: CameraBackgroundImage | None = (
            next((bg for bg in camera.background_images if bg.clip == color_movie_clip), None)
            if color_movie_clip is not None
            else None
        )

        color_movie_clip = self._import_texture(scene, camera_props.color_texture_props, f"{camera.name}.color").then()

        if camera_props.outer_scout_type == "PERSPECTIVE":
            if camera_background is None:
                camera_background = camera.background_images.new()
                camera_background.alpha = 1

            camera_background.source = "MOVIE_CLIP"
            camera_background.clip = color_movie_clip

        self._import_texture(scene, camera_props.depth_texture_props, f"{camera.name}.depth").then()

    @Result.do()
    def _import_texture(self, scene: Scene, texture_props: RenderTextureProperties, clip_id: str) -> MovieClip:
        if not texture_props.has_recording_path:
            return

        recording_path = texture_props.absolute_recording_path
        if not path.isfile(recording_path):
            Result.do_error(f'file "{texture_props.recording_path}" is not a file')

        movie_clip = texture_props.movie_clip
        if movie_clip:
            bpy.data.movieclips.remove(movie_clip, do_unlink=True)

        movie_clip = bpy.data.movieclips.load(recording_path)
        texture_props.movie_clip = movie_clip

        movie_clip.name = "outer_scout." + clip_id
        movie_clip.frame_start = scene.frame_start

        return movie_clip

