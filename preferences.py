from bpy.types import AddonPreferences
from bpy.props import StringProperty


class OWSceneImporterPreferences(AddonPreferences):
    bl_idname = __package__

    ow_bodies_folder : StringProperty(
        name="Outer Wilds exported bodies folder",
        description="Folder that contains .fbx files of OW bodies (use AssetStudio to get them).\nAddon will create .blend files there which are bodies with higher mesh quality",
        subtype="DIR_PATH",
    )

    ow_assets_folder : StringProperty(
        name="Outer Wilds extracted assets folder",
        description="Folder that contains OW assets (use AssetStudio to get them).\n Addon will use it to get higher resolution meshes",
        subtype="DIR_PATH",
    )

    ignored_objects: StringProperty(
        name="Ignored objects",
        description="Addon will ignore game objects that include one of these parts in their names",
        default="proxy,effect,fog,shockLayer,atmosphere,fadeBubble,whiteHoleSingularity"
    )

    def draw(self, _):
        self.layout.prop(self, "ow_bodies_folder")
        self.layout.prop(self, "ow_assets_folder")
        self.layout.prop(self, "ignored_objects")


__all__ = [OWSceneImporterPreferences]
