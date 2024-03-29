from bpy.props import BoolProperty, EnumProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import Camera, MovieClip, PropertyGroup

from ..bpy_register import bpy_register_property


@bpy_register_property(Camera, "outer_scout_camera")
class CameraProperties(PropertyGroup):
    outer_scout_type: EnumProperty(
        name="Outer Scout Type",
        default="NONE",
        items=[
            ("NONE", "None", ""),
            ("PERSPECTIVE", "Perspective", ""),
            ("EQUIRECTANGULAR", "Equirectangular", "Equirectangular camera used to record HDRI"),
        ],
        options=set(),
    )

    is_recording_enabled: BoolProperty(name="Recording Enabled", default=True)

    equirect_face_size: IntProperty(
        name="Equirectangular Face Size",
        description="Size of one side of the equirectangular video (only for equirectangular type)",
        default=1024,
        min=10,
        options=set(),
    )

    color_recording_path: StringProperty(
        name="Color Recording Path",
        description="The path to the file where the color recording will be saved",
        subtype="FILE_PATH",
        options=set(),
    )

    depth_recording_path: StringProperty(
        name="Depth Recording Path",
        description="The peth to the file where the depth recording will be saved",
        subtype="FILE_PATH",
        options=set(),
    )

    color_movie_clip: PointerProperty(
        name="Color Movie Clip",
        type=MovieClip,
        options=set(),
    )

    depth_movie_clip: PointerProperty(
        name="Depth Movie Clip",
        type=MovieClip,
        options=set(),
    )

    @staticmethod
    def of_camera(camera: Camera) -> "CameraProperties":
        return camera.outer_scout_camera

    @property
    def is_used_in_scene(self) -> bool:
        return self.outer_scout_type != "NONE" and self.is_recording_enabled

    @property
    def has_color_recording_path(self) -> bool:
        return self.color_recording_path != ""

    @property
    def has_depth_recording_path(self) -> bool:
        return self.outer_scout_type != "equirectangular" and self.depth_recording_path != ""

