from typing import TypeVar
from dataclasses import dataclass

from bpy.props import PointerProperty


TType = TypeVar("TType", bound=type)


@dataclass(frozen=True)
class RegisteredProperty:
    id_type: type
    property_name: str
    property_type: type


CLASSES_TO_REGISTER: list[type] = []


PROPERTIES_TO_REGISTER: dict[type, RegisteredProperty] = {}


def bpy_register(cls: TType) -> TType:
    CLASSES_TO_REGISTER.append(cls)
    return cls


def bpy_register_property(id_type: type, property_name: str, property_type=PointerProperty):
    def decorator(cls: TType) -> TType:
        CLASSES_TO_REGISTER.append(cls)
        PROPERTIES_TO_REGISTER[cls] = RegisteredProperty(id_type, property_name, property_type)
        return cls

    return decorator
