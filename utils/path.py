from os import path

from bpy.path import abspath as bpy_abspath
from bpy.types import Context


def get_footage_path(context: Context):
    return bpy_abspath(f"//Outer Wilds/footage/{context.scene.name}")


def get_camera_color_footage_path(context: Context, camera_index: int) -> str:
    return path.join(get_footage_path(context), "cameras", str(camera_index), "color.mp4")


def get_camera_depth_footage_path(context: Context, camera_index: int) -> str:
    return path.join(get_footage_path(context), "cameras", str(camera_index), "depth.mp4")


def get_hdri_video_path(context: Context) -> str:
    return path.join(get_footage_path(context), "hdri.mp4")
