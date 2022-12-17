bl_info = {
    "name": "outer-wilds-recorder-importer",
    "author": "Picalines",
    "description": "",
    "blender": (3, 3, 0),
    "version": (0, 0, 1),
    "location": "File > Import > OWScene",
    "warning": "",
    "category": "Import-Export",
}

import bpy
from . import addon

def menu_func_import(self, _):
    self.layout.operator(addon.OWSceneImporter.bl_idname, text="Outer Wilds recording (.owscene)")


def register():
    bpy.utils.register_class(addon.OWSceneImporter)
    bpy.utils.register_class(addon.OWSceneImporterPreferences)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(addon.OWSceneImporter)
    bpy.utils.unregister_class(addon.OWSceneImporterPreferences)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
