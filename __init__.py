bl_info = {
    "name": "outer-wilds-scene-recorder-blender",
    "author": "Picalines",
    "description": "",
    "blender": (4, 0, 0),
    "version": (0, 1, 0),
    "location": "View3D > Outer Wilds Recorder > ...",
    "warning": "",
    "category": "Compositing",
}

import bpy
from .bpy_register import BPY_CLASSES_TO_REGISTER, BPY_PROPERTIES_TO_REGISTER

from . import preferences as _
from . import properties as _
from . import panels as _
from . import operators as _


def register():
    registered_classes: set[type] = set()
    for cls in BPY_CLASSES_TO_REGISTER:
        if cls in registered_classes:
            continue

        bpy.utils.register_class(cls)
        registered_classes.add(cls)

        if cls in BPY_PROPERTIES_TO_REGISTER:
            registered_property = BPY_PROPERTIES_TO_REGISTER[cls]
            setattr(
                registered_property.id_type,
                registered_property.property_name,
                registered_property.property_type(type=cls),
            )


def unregister():
    for cls in BPY_CLASSES_TO_REGISTER:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
