bl_info = {
    "name": "outer-wilds-scene-recorder-blender",
    "author": "Picalines",
    "description": "",
    "blender": (3, 4, 0),
    "version": (0, 0, 1),
    "location": "View3D > Outer Wilds Recorder > ...",
    "warning": "",
    "category": "Compositing",
}

import bpy
from . import preferences
from . import panels
from . import operators


def iter_classes_to_register():
    yielded_classes = set()
    yield (preferences_cls := preferences.OWRecorderPreferences)
    yielded_classes.add(preferences_cls)
    for module, keys in map(lambda m: (m, dir(m)), (operators, panels)):
        for key in keys:
            if not (('_OT_' in key) or ('_PT_' in key)):
                continue
            if not isinstance(cls := getattr(module, key), type):
                continue
            if cls in yielded_classes:
                continue
            yield cls
            yielded_classes.add(cls)


def register():
    for cls in iter_classes_to_register():
        bpy.utils.register_class(cls)


def unregister():
    for cls in iter_classes_to_register():
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
