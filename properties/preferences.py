from bl_ui.generic_ui_list import draw_ui_list  # pyright: ignore [reportMissingImports]
from bpy.props import CollectionProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import AddonPreferences, Context, PropertyGroup

from ..bpy_register import bpy_load_post, bpy_register, bpy_register_post

ADDON_PACKAGE = __package__.split(".")[0]


@bpy_register
class IgnoredAssetPath(PropertyGroup):
    pass


@bpy_register
class IgnoredUnityLayer(PropertyGroup):
    pass


IGNORED_ASSET_PATHS_DEFAULT = [
    ":",
    "atmosphere",
    "darknessPlane",
    "decal",
    "effect",
    "fadeBubble",
    "fog",
    "lightbeam",
    "normals",
    "proxy",
    "shockLayer",
    "stencil",
    "targetPlane",
    "whiteHoleSingularity",
]


IGNORED_LAYERS_DEFAULT = ["DreamSimulation"]


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

    import_ignore_paths: CollectionProperty(
        name="Ignore Paths",
        type=IgnoredAssetPath,
    )

    import_ignore_paths_active_index: IntProperty(
        name="Ignored Asset Path",
        description="If the path to the asset contains at least one substring from the list, the asset is skipped",
    )

    import_ignore_layers: CollectionProperty(
        name="Ignore Layers",
        type=IgnoredUnityLayer,
    )

    import_ignore_layers_active_index: IntProperty(
        name="Ignored Unity Layer",
        description="If the asset is located on one of the Unity layers from the list, it is skipped",
    )

    modal_timer_delay: FloatProperty(
        name="Modal Delay",
        description="Time interval in seconds. Controls how often the addon will ask Outer Wilds about the recording progress",
        default=0.1,
        min=0.001,
        options=set(),
    )

    @staticmethod
    def from_context(context: Context) -> "OuterScoutPreferences":
        return context.preferences.addons[ADDON_PACKAGE].preferences

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        mod_panel_header, mod_panel = layout.panel(f"{self.bl_idname}.mod", default_closed=False)
        mod_panel_header.label(text="Mod Integration")

        if mod_panel:
            mod_panel.prop(self, "api_port")

        assets_panel_header, assets_panel = layout.panel(f"{self.bl_idname}.paths", default_closed=False)
        assets_panel_header.label(text="Asset Folders")

        if assets_panel:
            assets_panel.prop(self, "ow_bodies_folder", icon="ERROR" if not self.ow_bodies_folder else "NONE")
            assets_panel.prop(self, "ow_assets_folder", icon="ERROR" if not self.ow_assets_folder else "NONE")

            if not (self.ow_bodies_folder and self.ow_assets_folder):
                assets_panel.box().label(text="Folder paths are required for planet .blend generation", icon="ERROR")

        unity_panel_header, unity_panel = layout.panel(f"{self.bl_idname}.unity", default_closed=True)
        unity_panel_header.label(text="Ignored Unity Objects")

        if unity_panel:
            ignore_lists_row = unity_panel.row()

            ignore_paths_col = ignore_lists_row.column()
            ignore_paths_col.label(text="Asset Path")

            prefs_path = f'preferences.addons["{ADDON_PACKAGE}"].preferences'
            draw_ui_list(
                ignore_paths_col,
                context,
                list_path=f"{prefs_path}.import_ignore_paths",
                active_index_path=f"{prefs_path}.import_ignore_paths_active_index",
                unique_id=f"{self.bl_idname}.import_ignore_paths",
            )

            ignore_layers_col = ignore_lists_row.column()
            ignore_layers_col.label(text="Unity Layer")
            draw_ui_list(
                ignore_layers_col,
                context,
                list_path=f"{prefs_path}.import_ignore_layers",
                active_index_path=f"{prefs_path}.import_ignore_layers_active_index",
                unique_id=f"{self.bl_idname}.import_ignore_layers",
            )

        misc_panel_header, misc_panel = layout.panel(f"{self.bl_idname}.misc", default_closed=True)
        misc_panel_header.label(text="Miscellaneous")

        if misc_panel:
            misc_panel.prop(self, "modal_timer_delay")

    @property
    def has_file_paths(self) -> bool:
        return bool(self.ow_bodies_folder) and bool(self.ow_assets_folder)


@bpy_load_post
@bpy_register_post
def set_default_lists_in_preferences():
    import bpy

    preferences = OuterScoutPreferences.from_context(bpy.context)

    should_set_defaults = not preferences.import_ignore_paths and not preferences.import_ignore_layers

    if should_set_defaults:
        for path_value in IGNORED_ASSET_PATHS_DEFAULT:
            ignored_path = preferences.import_ignore_paths.add()
            ignored_path.name = path_value

        for layer_name in IGNORED_LAYERS_DEFAULT:
            ignored_layer = preferences.import_ignore_layers.add()
            ignored_layer.name = layer_name
