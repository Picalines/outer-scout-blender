from bpy.props import EnumProperty, IntProperty, PointerProperty
from bpy.types import Camera, MovieClip, PropertyGroup

from ..bpy_register import bpy_register_property


@bpy_register_property(Camera, "outer_scout_camera")
class CameraProperties(PropertyGroup):
    outer_scout_type = (
        EnumProperty(
            name="Outer Scout Type",
            default="",
            items=[
                ("", "None", ""),
                ("perspective", "Perspective", ""),
                ("equirectangular", "Equirectangular", "Equirectangular camera used to record HDRI"),
            ],
        ),
    )

    equirect_face_size: IntProperty(
        name="Equirectangular Face Size",
        description="Size of one side of the equirectangular video (only for equirectangular type)",
        default=1024,
        min=10,
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

