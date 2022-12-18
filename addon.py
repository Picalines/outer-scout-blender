from math import radians

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator
from mathutils import Euler

from .preferences import OWSceneImporterPreferences
from .ui_utils import show_message_box
from .object_utils import set_parent, create_empty
from .ow_camera import create_camera
from .ow_ground_body import load_ground_body
from .ow_scene_data import load_ow_scene_data, apply_transform_data, apply_scene_settings
from .compositor_nodes import set_compositor_nodes
from .world_nodes import set_world_nodes


class OWSceneImporter(Operator, ImportHelper):
    bl_idname = 'outer_wilds_recorder.importer'
    bl_label = 'Import .owscene'

    filename_ext = '.owscene'

    filter_glob : StringProperty(
        default = '*.owscene',
        options = { 'HIDDEN' },
        maxlen = 255
    )

    def execute(self, context):
        preferences: OWSceneImporterPreferences = context.preferences.addons[__package__].preferences

        ow_data = load_ow_scene_data(self.filepath)

        # create body pivot
        ow_player_pivot = create_empty()
        ow_player_pivot.name = 'OW_PlayerPivot'
        apply_transform_data(ow_player_pivot, ow_data['player']['transform'])

        # create player camera pivot
        player_camera_pivot = create_empty()
        player_camera_pivot.name = 'PlayerCamera_Pivot'
        apply_transform_data(player_camera_pivot, ow_data['player_camera']['transform'])

        # create camera
        camera = create_camera(self.filepath, context.scene, ow_data)

        # import ground_body
        ow_ground_body = load_ground_body(ow_data, preferences)
        if not ow_ground_body:
            show_message_box(context, f"ground body is not loaded ({ow_data['ground_body']['name']}.blend not found)")

        # move scene to origin
        set_parent(context, [camera, player_camera_pivot, ow_ground_body], ow_player_pivot, keep_transform=True)
        ow_player_pivot.location = (0, 0, 0)

        # make X - right, Y - forward, Z - up
        # (like in new General project)
        ow_player_pivot.rotation_mode = 'XYZ'
        ow_player_pivot.rotation_euler = Euler((radians(90), 0, radians(90)), 'XYZ')

        # scene properties
        apply_scene_settings(context, context.scene, ow_data)

        # nodes
        set_world_nodes(self.filepath, context.scene, ow_data)
        set_compositor_nodes(self.filepath, context.scene, ow_data)

        return {'FINISHED'}
