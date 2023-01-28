bl_info = {
    "name": "outer-wilds-recorder-blender",
    "author": "Picalines",
    "description": "",
    "blender": (3, 4, 0),
    "version": (0, 0, 1),
    "location": "View3D > Outer Wilds Recorder > ...",
    "warning": "",
    "category": "Compositing",
}

import bpy
from . import addon
from . import panels
from . import ow_ground_body


def register():
    bpy.utils.register_class(addon.OWSceneImporter)
    bpy.utils.register_class(ow_ground_body.OWRECORDER_OT_generate_ground_body)
    bpy.utils.register_class(ow_ground_body.OWRECORDER_OT_generate_ground_body_background)
    bpy.utils.register_class(addon.OWSceneImporterPreferences)
    bpy.utils.register_class(panels.OWRECORDER_PT_sync_tools)


def unregister():
    bpy.utils.unregister_class(addon.OWSceneImporter)
    bpy.utils.unregister_class(ow_ground_body.OWRECORDER_OT_generate_ground_body)
    bpy.utils.unregister_class(ow_ground_body.OWRECORDER_OT_generate_ground_body_background)
    bpy.utils.unregister_class(addon.OWSceneImporterPreferences)
    bpy.utils.unregister_class(panels.OWRECORDER_PT_sync_tools)


if __name__ == "__main__":
    register()
