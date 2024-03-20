from bpy.props import IntProperty, StringProperty
from bpy.types import AddonPreferences, Context

from ..bpy_register import bpy_register

ADDON_PACKAGE = __package__.split(".")[0]


@bpy_register
class OuterScoutPreferences(AddonPreferences):
    bl_idname = ADDON_PACKAGE

    api_port: IntProperty(
        name="API port",
        description="Add-on communicates with the Outer Scout mod through localhost at this port.\n"
        + "Should be same as in the mod settings",
        default=2209,
    )

    ow_bodies_folder: StringProperty(
        name="Bodies Folder",
        description="Folder that contains .fbx and .blend files of Outer Wilds planets (bodies)",
        subtype="DIR_PATH",
    )

    ow_assets_folder: StringProperty(
        name="Extracted Assets Folder",
        description="Folder that contains Outer Wilds assets",
        subtype="DIR_PATH",
    )

    ignored_objects: StringProperty(
        name="Ignored objects",
        description="Addon will ignore game objects that include one of these parts in their names",
        default="proxy,effect,fog,shockLayer,atmosphere,fadeBubble,whiteHoleSingularity,normals",
    )

    @staticmethod
    def from_context(context: Context) -> "OuterScoutPreferences":
        return context.preferences.addons[ADDON_PACKAGE].preferences

    def draw(self, _):
        self.layout.use_property_split = True

        self.layout.prop(self, "api_port")
        self.layout.prop(self, "ow_bodies_folder")
        self.layout.prop(self, "ow_assets_folder")
        self.layout.prop(self, "ignored_objects")

    def are_valid(self) -> bool:
        return bool(self.ow_bodies_folder) and bool(self.ow_assets_folder)

