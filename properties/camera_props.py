from bpy.props import BoolProperty, EnumProperty, IntProperty, PointerProperty
from bpy.types import Camera, Image, NodeTree, PropertyGroup

from ..bpy_register import bpy_register_property
from .render_texture_props import RenderTextureProperties


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

    color_texture_settings: PointerProperty(type=RenderTextureProperties)

    depth_texture_settings: PointerProperty(type=RenderTextureProperties)

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
    def color_texture_props(self) -> RenderTextureProperties:
        return self.color_texture_settings

    @property
    def depth_texture_props(self) -> RenderTextureProperties:
        return self.depth_texture_settings

    @property
    def has_any_recording_path(self) -> bool:
        return self.color_texture_props.has_recording_path or self.depth_texture_props.has_recording_path

