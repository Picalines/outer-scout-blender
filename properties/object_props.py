from bpy.props import BoolProperty, StringProperty
from bpy.types import Object, PropertyGroup

from ..bpy_register import bpy_register_property


@bpy_register_property(Object, "outer_scout_object")
class ObjectProperties(PropertyGroup):
    outer_wilds_name: StringProperty(
        name="Outer Wilds Name", description="The name of the GameObject from Outer Wilds", default="", options=set()
    )

    record_transform: BoolProperty(
        name="Record Transform",
        description="If true, the add-on will record the transformation of the GameObject and apply it in Blender",
        default=False,
        options=set(),
    )

    @staticmethod
    def of_object(object: Object) -> "ObjectProperties":
        return object.outer_scout_object

