from dataclasses import dataclass
from typing import Callable, TypeVar

from bpy.props import PointerProperty

TType = TypeVar("TType", bound=type)


@dataclass(frozen=True)
class RegisteredProperty:
    id_type: type
    property_name: str
    property_type: type


CLASSES_TO_REGISTER: list[type] = []


PROPERTIES_TO_REGISTER: dict[type, RegisteredProperty] = {}


PANEL_EXTENSIONS_TO_REGISTER: dict[type, list[Callable]] = {}


def bpy_register(cls: TType) -> TType:
    CLASSES_TO_REGISTER.append(cls)
    return cls


def bpy_register_property(id_type: type, property_name: str, property_type=PointerProperty):
    def decorator(cls: TType) -> TType:
        CLASSES_TO_REGISTER.append(cls)
        PROPERTIES_TO_REGISTER[cls] = RegisteredProperty(id_type, property_name, property_type)
        return cls

    return decorator


def bpy_extend_panel(panel_type: type):
    def decorator(draw: Callable) -> Callable:
        draw_funcs = PANEL_EXTENSIONS_TO_REGISTER.setdefault(panel_type, [])
        draw_funcs.append(draw)
        return draw

    return decorator

