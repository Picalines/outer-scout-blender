from bpy.props import BoolProperty, EnumProperty, IntProperty, PointerProperty
from bpy.types import Camera, Image, NodeTree, PropertyGroup

from ..bpy_register import bpy_register_property
from .texture_recording_props import TextureRecordingProperties


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

    is_recording_enabled: BoolProperty(name="Recording Enabled", default=True, options=set())

    equirect_face_size: IntProperty(
        name="Equirectangular Face Size",
        description="Size of one side of the equirectangular video (only for equirectangular type)",
        default=1024,
        min=10,
        options=set(),
    )

    color_texture_recording: PointerProperty(type=TextureRecordingProperties)

    depth_texture_recording: PointerProperty(type=TextureRecordingProperties)

    hdri_image: PointerProperty(
        name="HDRI Image",
        type=Image,
        options=set(),
    )

    hdri_node_group: PointerProperty(
        name="HDRI Node Group",
        type=NodeTree,
        options=set(),
    )

    @staticmethod
    def of_camera(camera: Camera) -> "CameraProperties":
        return camera.outer_scout_camera

    @property
    def is_active(self) -> bool:
        return self.outer_scout_type != "NONE" and self.is_recording_enabled

    @property
    def color_texture_props(self) -> TextureRecordingProperties:
        return self.color_texture_recording

    @property
    def depth_texture_props(self) -> TextureRecordingProperties:
        return self.depth_texture_recording

    @property
    def has_any_recording_path(self) -> bool:
        return self.color_texture_props.has_recording_path or self.depth_texture_props.has_recording_path

