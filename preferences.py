from bpy.types import AddonPreferences, Context
from bpy.props import StringProperty, IntProperty

from .bpy_register import bpy_register


@bpy_register
class OWRecorderPreferences(AddonPreferences):
    bl_idname = __package__

    api_port : IntProperty(
        name='API port',
        description='Addon communicates with the SceneRecorder mod through localhost at this port.\n'
            + 'Should be same as in the mod settings',
        default=5000
    )

    ow_bodies_folder : StringProperty(
        name='Outer Wilds exported bodies folder',
        description='Folder that contains .fbx files of OW bodies (use AssetStudio to get them).\n'
            + 'Addon will create .blend files there which are bodies with higher mesh quality',
        subtype='DIR_PATH',
    )

    ow_assets_folder : StringProperty(
        name='Outer Wilds extracted assets folder',
        description='Folder that contains OW assets (use AssetStudio to get them).\n'
            + 'Addon will use it to get higher resolution meshes',
        subtype='DIR_PATH',
    )

    ignored_objects: StringProperty(
        name='Ignored objects',
        description='Addon will ignore game objects that include one of these parts in their names',
        default='proxy,effect,fog,shockLayer,atmosphere,fadeBubble,whiteHoleSingularity'
    )

    @staticmethod
    def from_context(context: Context) -> 'OWRecorderPreferences':
        return context.preferences.addons[__package__].preferences

    def empty(self) -> bool:
        return (not self.ow_bodies_folder) or (not self.ow_assets_folder)

    def draw(self, _):
        self.layout.prop(self, 'api_port')
        self.layout.prop(self, 'ow_bodies_folder')
        self.layout.prop(self, 'ow_assets_folder')
        self.layout.prop(self, 'ignored_objects')
