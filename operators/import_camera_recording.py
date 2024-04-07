from os import path

import bpy
from bpy.types import Camera, CameraBackgroundImage, MovieClip, Object, Operator, Scene

from ..bpy_register import bpy_register
from ..properties import CameraProperties, TextureRecordingProperties
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

        color_movie_clip = self._import_texture(scene, camera_props.color_texture_props, f"{camera.name}.color").then()
        self._import_texture(scene, camera_props.depth_texture_props, f"{camera.name}.depth").then()

        if camera_props.outer_scout_type == "PERSPECTIVE":
            camera_background: CameraBackgroundImage | None = next(
                (bg for bg in camera.background_images if bg.clip and bg.clip.name == color_movie_clip.name), None
            )

            if camera_background is None:
                camera_background = camera.background_images.new()
                camera_background.alpha = 1
                camera_background.source = "MOVIE_CLIP"
                camera_background.clip = color_movie_clip

    @Result.do()
    def _import_texture(self, scene: Scene, texture_props: TextureRecordingProperties, clip_id: str) -> MovieClip:
        if not texture_props.has_recording_path:
            return

        recording_path = texture_props.absolute_recording_path
        if not path.isfile(recording_path):
            Result.do_error(f'file "{texture_props.recording_path}" is not a file')

        old_movie_clip: MovieClip = texture_props.movie_clip
        new_movie_clip = bpy.data.movieclips.load(recording_path)

        if old_movie_clip is not None:
            old_name = old_movie_clip.name
            old_movie_clip.user_remap(new_movie_clip)
            bpy.data.movieclips.remove(old_movie_clip)
            new_movie_clip.name = old_name
        else:
            new_movie_clip.name = "outer_scout." + clip_id

        texture_props.movie_clip = new_movie_clip
        new_movie_clip.frame_start = scene.frame_start

        return new_movie_clip

