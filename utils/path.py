from os import path

from bpy.path import abspath as bpy_abspath
from bpy.types import Context


def get_footage_path(context: Context):
    return bpy_abspath(f"//Outer Wilds/footage/{context.scene.name}")


def get_background_video_path(context: Context) -> str:
    return path.join(get_footage_path(context), "background.mp4")


def get_depth_video_path(context: Context) -> str:
    return path.join(get_footage_path(context), "depth.mp4")


def get_hdri_video_path(context: Context) -> str:
    return path.join(get_footage_path(context), "hdri.mp4")
