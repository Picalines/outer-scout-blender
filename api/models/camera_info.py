from bpy.types import Camera

from math import radians, degrees
from typing import TypedDict


class CameraInfo(TypedDict):
    fov: float
    near_clip_plane: float
    far_clip_plane: float


def camera_info_from_blender(camera: Camera):
    return CameraInfo(
        fov=degrees(camera.angle),
        near_clip_plane=camera.clip_start,
        far_clip_plane=camera.clip_end,
    )


def apply_camera_info(camera: Camera, info: CameraInfo):
    camera.type = 'PERSP'
    camera.lens_unit = 'FOV'
    camera.sensor_fit = 'VERTICAL'

    camera.angle = radians(info['fov'])
    camera.clip_start = info['near_clip_plane']
    camera.clip_end = info['far_clip_plane']
