from bpy.props import PointerProperty, StringProperty
from bpy.types import Object, PropertyGroup

from ..bpy_register import bpy_register_property
from .transform_recording_props import TransformRecordingProperties


@bpy_register_property(Object, "outer_scout_object")
class ObjectProperties(PropertyGroup):
    unity_object_name: StringProperty(
        name="Unity Object Name", description="The name of the GameObject from Outer Wilds", default="", options=set()
    )

    transform_recording: PointerProperty(type=TransformRecordingProperties)

    @staticmethod
    def of_object(object: Object) -> "ObjectProperties":
        return object.outer_scout_object

    @property
    def transform_props(self) -> "TransformRecordingProperties":
        return self.transform_recording

    @property
    def has_unity_object_name(self) -> bool:
        return self.unity_object_name != ""

