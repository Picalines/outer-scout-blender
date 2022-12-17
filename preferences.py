from bpy.types import AddonPreferences
from bpy.props import StringProperty


class OWSceneImporterPreferences(AddonPreferences):
    bl_idname = __package__

    ow_bodies_folder : StringProperty(
        name = "Outer Wilds exported bodies folder",
        description = "Use AssetStudio to get that",
        subtype = "DIR_PATH",
    )

    ow_assets_folder : StringProperty(
        name = "Outer Wilds extracted meshes folder",
        description = "Use AssetStudio to get that",
        subtype = "DIR_PATH",
    )

    def draw(self, _):
        self.layout.label(text="This is a preferences view for our add-on")
        self.layout.prop(self, "ow_bodies_folder")
        self.layout.prop(self, "ow_assets_folder")


__all__ = [OWSceneImporterPreferences]
