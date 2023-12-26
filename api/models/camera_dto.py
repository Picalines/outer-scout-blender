from typing import TypedDict

import bpy
from bpy.types import Camera


class CameraDTO(TypedDict):
    sensorSize: tuple[float, float]
    focalLength: float
    lensShift: tuple[float, float]
    nearClipPlane: float
    farClipPlane: float
    gateFit: str


def get_camera_dto(camera: Camera) -> CameraDTO:
    camera.lens_unit = "MILLIMETERS"

    return {
        "sensorSize": (camera.sensor_width, camera.sensor_height),
        "focalLength": camera.lens,
        "lensShift": (camera.shift_x, camera.shift_y),
        "nearClipPlane": camera.clip_start,
        "farClipPlane": camera.clip_end,
        "gateFit": get_unity_gate_fit(),
    }


def apply_camera_dto(camera: Camera, info: CameraDTO):
    camera.type = "PERSP"

    camera.lens_unit = "MILLIMETERS"
    camera.lens = info["focalLength"]

    camera.shift_x, camera.shift_y = info["lensShift"]

    camera.sensor_fit = info["gateFit"].upper()
    camera.sensor_width, camera.sensor_height = info["sensorSize"]

    camera.clip_start = info["nearClipPlane"]
    camera.clip_end = info["farClipPlane"]


def get_unity_gate_fit():
    render_settings = bpy.context.scene.render
    width, height = render_settings.resolution_x, render_settings.resolution_y

    if width >= height:
        return "Horizontal"

    return "Vertical"

