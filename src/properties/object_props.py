from bpy.props import EnumProperty, PointerProperty, StringProperty
from bpy.types import Object, PropertyGroup

from ..bpy_register import bpy_register_property
from .transform_recording_props import TransformRecordingProperties


def on_unity_object_name_update(object_props: "ObjectProperties", _):
    if object_props.unity_object_name.startswith("__"):
        object_props.unity_object_name = object_props.unity_object_name.removeprefix("__")

    if "/" in object_props.unity_object_name:
        object_props.unity_object_name = object_props.unity_object_name.replace("/", "_")


@bpy_register_property(Object, "outer_scout_object")
class ObjectProperties(PropertyGroup):
    unity_object_name: StringProperty(
        name="Unity Object Name",
        description="The name of the GameObject from Outer Wilds",
        default="",
        options=set(),
        update=on_unity_object_name_update,
    )

    object_type: EnumProperty(
        name="Unity Object Mode",
        default="CUSTOM",
        items=[
            ("CUSTOM", "Custom", "Creates new empty GameObject in Unity"),
            ("EXISTING", "Existing", "Uses existing Unity GameObject"),
        ],
        options=set(),
    )

    transform_recording: PointerProperty(type=TransformRecordingProperties, options=set())

    @staticmethod
    def of_object(object: Object) -> "ObjectProperties":
        return object.outer_scout_object

    @property
    def transform_props(self) -> "TransformRecordingProperties":
        return self.transform_recording

    @property
    def has_unity_object_name(self) -> bool:
        return self.unity_object_name != ""
