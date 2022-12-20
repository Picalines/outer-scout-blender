from math import radians
from mathutils import Quaternion
from pathlib import Path

import bpy
from bpy.types import Scene, Camera

from .ow_json_data import OWSceneData, apply_transform_data


def create_camera(owscene_filepath: str, scene: Scene, ow_data: OWSceneData):
    bpy.ops.object.camera_add()
    camera = scene.camera = bpy.context.active_object

    camera_data: Camera = camera.data
    camera_data.type = 'PERSP'
    camera_data.lens_unit = 'FOV'
    camera_data.sensor_fit = 'VERTICAL'
    camera_data.angle = radians(ow_data['background_camera']['fov'])

    background_video_path = str(Path(owscene_filepath).parent.joinpath('background.mp4'))

    camera_data.show_background_images = True
    camera_background = camera_data.background_images.new()
    camera_background.source = 'MOVIE_CLIP'
    camera_background.clip = bpy.data.movieclips.load(background_video_path)
    camera_background.clip.name = 'OW_mainCamera'
    camera_background.alpha = 1

    scene.render.resolution_x, scene.render.resolution_y = camera_background.clip.size

    camera.name = 'OW Camera'
    apply_transform_data(camera, ow_data['background_camera']['transform'])
    camera.rotation_quaternion @= Quaternion((0, 1, 0), -radians(90))

    return camera
