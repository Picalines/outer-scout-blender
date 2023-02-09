from typing import TypeVar
from dataclasses import dataclass

from bpy.props import PointerProperty


TType = TypeVar('TType', bound=type)


@dataclass
class RegisteredProperty:
    id_type: type
    property_name: str
    property_type: type


CLASSES_TO_REGISTER: set[type] = set()


PROPERTIES_TO_REGISTER: dict[type, RegisteredProperty] = {}


def bpy_register(cls: TType) -> TType:
    CLASSES_TO_REGISTER.add(cls)
    return cls


def bpy_register_property(id_type: type, property_name: str, property_type: type = PointerProperty):
    def decorator(cls: TType) -> TType:
        CLASSES_TO_REGISTER.add(cls)
        PROPERTIES_TO_REGISTER[cls] = RegisteredProperty(id_type, property_name, property_type)
        return cls

    return decorator
