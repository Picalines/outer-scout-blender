from bpy.path import abspath
from bpy.props import IntProperty, PointerProperty, StringProperty
from bpy.types import MovieClip, PropertyGroup

from ..bpy_register import bpy_register


@bpy_register
class TextureRecordingProperties(PropertyGroup):
    recording_path: StringProperty(
        name="Recording Path",
        description="The path to the file where the texture recording will be saved",
        subtype="FILE_PATH",
        default="",
        options=set(),
    )

    constant_rate_factor: IntProperty(
        name="Constant Rate Factor",
        description="FFmpeg setting that controls the level of video compression. A low value means higher quality but also higher disk usage",
        default=18,
        min=0,
        max=63,
        options=set(),
    )

    movie_clip: PointerProperty(
        name="Movie Clip",
        type=MovieClip,
        options=set(),
    )

    @property
    def has_recording_path(self) -> bool:
        return self.recording_path != ""

    @property
    def absolute_recording_path(self) -> str:
        return abspath(self.recording_path)
