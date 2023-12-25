from bpy.types import Camera

from typing import TypedDict


class CameraDTO(TypedDict):
    sensor_size: tuple[float, float]
    focal_length: float
    lens_shift: tuple[float, float]
    near_clip_plane: float
    far_clip_plane: float


def camera_info_from_blender(camera: Camera):
    return CameraDTO(
        sensor_size=(camera.sensor_width, camera.sensor_height),
        focal_length=camera.lens,
        lens_shift=(camera.shift_x, camera.shift_y),
        near_clip_plane=camera.clip_start,
        far_clip_plane=camera.clip_end,
    )


def apply_camera_info(camera: Camera, info: CameraDTO):
    camera.type = "PERSP"
    camera.lens_unit = "MILLIMETERS"

    camera.lens = info["focal_length"]
    camera.shift_x, camera.shift_y = info["lens_shift"]
    camera.sensor_width, camera.sensor_height = info["sensor_size"]
    camera.clip_start = info["near_clip_plane"]
    camera.clip_end = info["far_clip_plane"]
