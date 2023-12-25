from bpy.types import Camera

from typing import TypedDict


class CameraDTO(TypedDict):
    sensorSize: tuple[float, float]
    focalLength: float
    lensShift: tuple[float, float]
    nearClipPlane: float
    farClipPlane: float


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

    camera.lens = info["focalLength"]
    camera.shift_x, camera.shift_y = info["lensShift"]
    camera.sensor_width, camera.sensor_height = info["sensorSize"]
    camera.clip_start = info["nearClipPlane"]
    camera.clip_end = info["farClipPlane"]
