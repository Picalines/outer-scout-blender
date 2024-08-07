import importlib
import sys

import bpy


def register():
    reload_addon()

    from . import properties as _
    from . import operators as _
    from . import panels as _
    from .bpy_register import (
        CLASSES_TO_REGISTER,
        LOAD_POST_HANDLERS_TO_REGISTER,
        PANEL_EXTENSIONS_TO_REGISTER,
        PROPERTIES_TO_REGISTER,
        REGISTER_POST_HANDLERS_TO_CALL,
    )

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

    for load_post_handler in LOAD_POST_HANDLERS_TO_REGISTER:
        bpy.app.handlers.load_post.append(load_post_handler)

    for register_post_handler in REGISTER_POST_HANDLERS_TO_CALL:
        try:
            register_post_handler()
        except Exception as exception:
            print("[outer_scout]", exception)


def unregister():
    from .bpy_register import (
        CLASSES_TO_REGISTER,
        LOAD_POST_HANDLERS_TO_REGISTER,
        PANEL_EXTENSIONS_TO_REGISTER,
        PROPERTIES_TO_REGISTER,
    )

    for cls in CLASSES_TO_REGISTER:
        if cls in PROPERTIES_TO_REGISTER:
            registered_property = PROPERTIES_TO_REGISTER[cls]
            delattr(registered_property.id_type, registered_property.property_name)

        bpy.utils.unregister_class(cls)

    for panel_type, draw_funcs in PANEL_EXTENSIONS_TO_REGISTER.items():
        for draw_func in reversed(draw_funcs):
            panel_type.remove(draw_func)

    for load_post_handler in LOAD_POST_HANDLERS_TO_REGISTER:
        bpy.app.handlers.load_post.remove(load_post_handler)


def reload_addon():
    module_prefix = f"{__name__}."
    for name, submodule in sys.modules.copy().items():
        if name.startswith(module_prefix):
            importlib.reload(submodule)


if __name__ == "__main__":
    register()
