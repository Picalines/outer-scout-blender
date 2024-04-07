from bpy.props import EnumProperty, StringProperty
from bpy.types import Object, PropertyGroup

from ..bpy_register import bpy_register_property


@bpy_register_property(Object, "outer_scout_object")
class ObjectProperties(PropertyGroup):
    transform_recording_path: StringProperty(
        name="Transform Recording Path",
        description="The path to the file where the transform recording (json) will be saved",
        subtype="FILE_PATH",
        default="",
    )

    unity_object_name: StringProperty(
        name="Unity Object Name", description="The name of the GameObject from Outer Wilds", default="", options=set()
    )

    transform_mode: EnumProperty(
        name="Transform Mode",
        default="RECORD",
        items=[
            ("RECORD", "Record", "Record Unity object transform and import it as keyframes of this object"),
            ("REPLAY", "Replay", "Send this object's transform keyframes to Outer Wilds"),
        ],
        options=set(),
    )

    @staticmethod
    def of_object(object: Object) -> "ObjectProperties":
        return object.outer_scout_object

    @property
    def has_transform_recording_path(self):
        return self.transform_recording_path != ""

    @property
    def is_used_in_scene(self):
        return self.unity_object_name != "" and self.transform_recording_path != ""

