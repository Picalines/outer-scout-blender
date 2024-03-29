from bpy.props import IntProperty, StringProperty
from bpy.types import AddonPreferences, Context

from ..bpy_register import bpy_register

ADDON_PACKAGE = __package__.split(".")[0]


@bpy_register
class OuterScoutPreferences(AddonPreferences):
    bl_idname = ADDON_PACKAGE

    api_port: IntProperty(
        name="API port",
        description="Add-on communicates with the Outer Scout mod through localhost at this port. Should be same as in the mod settings",
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

    import_ignore_paths: StringProperty(
        name="Ignore Paths",
        description="The list is separated by commas. If the path to the asset contains at least one substring from the list, the asset is skipped ",
        default=":,proxy,effect,fog,decal,shockLayer,atmosphere,fadeBubble,whiteHoleSingularity,normals,darknessPlane,targetPlane,lightbeam,stencil",
    )

    import_ignore_layers: StringProperty(
        name="Ignore Layers",
        description="The list is separated by commas. If the asset is located on one of the Unity layers from the list, it is skipped",
        default="DreamSimulation",
    )

    @staticmethod
    def from_context(context: Context) -> "OuterScoutPreferences":
        return context.preferences.addons[ADDON_PACKAGE].preferences

    def draw(self, _):
        self.layout.use_property_split = True

        self.layout.prop(self, "api_port")
        self.layout.prop(self, "ow_bodies_folder")
        self.layout.prop(self, "ow_assets_folder")
        self.layout.prop(self, "import_ignore_paths")
        self.layout.prop(self, "import_ignore_layers")

    @property
    def are_valid(self) -> bool:
        return bool(self.ow_bodies_folder) and bool(self.ow_assets_folder)

