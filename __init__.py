bl_info = {
    "name": "outer-scout-blender",
    "author": "picalines",
    "description": "A cinematic toolbox for Outer Wilds & Blender",
    "blender": (4, 1, 0),
    "version": (0, 1, 0),
    "category": "Compositing",
}

import importlib
import sys

import bpy


def register():
    reload_addon()

    from . import operators as _
    from . import panels as _
    from . import properties as _
    from .bpy_register import CLASSES_TO_REGISTER, PANEL_EXTENSIONS_TO_REGISTER, PROPERTIES_TO_REGISTER

    registered_classes: set[type] = set()
    for cls in CLASSES_TO_REGISTER:
        if cls in registered_classes:
            continue

        bpy.utils.register_class(cls)
        registered_classes.add(cls)

        if cls in PROPERTIES_TO_REGISTER:
            registered_property = PROPERTIES_TO_REGISTER[cls]
            setattr(
                registered_property.id_type,
                registered_property.property_name,
                registered_property.property_type(type=cls),
            )

    for panel_type, draw_funcs in PANEL_EXTENSIONS_TO_REGISTER.items():
        for draw_func in draw_funcs:
            panel_type.append(draw_func)


def unregister():
    from .bpy_register import CLASSES_TO_REGISTER, PANEL_EXTENSIONS_TO_REGISTER, PROPERTIES_TO_REGISTER

    for cls in CLASSES_TO_REGISTER:
        if cls in PROPERTIES_TO_REGISTER:
            registered_property = PROPERTIES_TO_REGISTER[cls]
            delattr(registered_property.id_type, registered_property.property_name)

        bpy.utils.unregister_class(cls)

    for panel_type, draw_funcs in PANEL_EXTENSIONS_TO_REGISTER.items():
        for draw_func in reversed(draw_funcs):
            panel_type.remove(draw_func)


def reload_addon():
    module_prefix = f"{__name__}."
    for name, submodule in sys.modules.copy().items():
        if name.startswith(module_prefix):
            importlib.reload(submodule)


if __name__ == "__main__":
    register()

