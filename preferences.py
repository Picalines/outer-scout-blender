from bpy.types import AddonPreferences
from bpy.props import StringProperty


class OWSceneImporterPreferences(AddonPreferences):
    bl_idname = __package__

    ow_bodies_folder : StringProperty(
        name = "Outer Wilds exported bodies folder",
        description = "Folder that contains .fbx files of OW bodies (use AssetStudio to get them).\nAddon will create .blend files there which are bodies with higher mesh quality",
        subtype = "DIR_PATH",
    )

    ow_assets_folder : StringProperty(
        name = "Outer Wilds extracted assets folder",
        description = "Folder that contains OW assets (use AssetStudio to get them).\n Addon will use it to get higher resolution meshes",
        subtype = "DIR_PATH",
    )

    def draw(self, _):
        self.layout.label(text="This is a preferences view for our add-on")
        self.layout.prop(self, "ow_bodies_folder")
        self.layout.prop(self, "ow_assets_folder")


__all__ = [OWSceneImporterPreferences]
