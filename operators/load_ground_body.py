import subprocess
import json
from pathlib import Path
from typing import Iterable

import bpy
from bpy.types import Operator, Object, Context
from bpy.props import EnumProperty

from ..preferences import OWRecorderPreferences
from ..api import APIClient
from .ground_body_selection_helper import GroundBodySelectionHelper


GROUND_BODY_COLLECTION_NAME = 'Outer Wilds ground body'


def get_current_ground_body() -> Object | None:
    if GROUND_BODY_COLLECTION_NAME not in bpy.data.collections:
        return None
    ground_body_collection = bpy.data.collections[GROUND_BODY_COLLECTION_NAME]
    return ground_body_collection.objects[0] if any(ground_body_collection.objects) else None


class OW_RECORDER_OT_load_ground_body(Operator, GroundBodySelectionHelper):
    '''Loads current ground body (might take a while for the first time) and links it to current project.'''

    bl_idname = 'ow_recorder.load_ground_body'
    bl_label = 'Load ground body'

    sector_loading_mode: EnumProperty(
        name='Sector Mode',
        items=[
            ('CURRENT_AND_PARENTS', 'Current And Parents', ''),
            ('CURRENT', 'Only Current', ''),
            ('ALL', 'All', '(potential high RAM usage)'),
        ],
    )

    def execute(self, context: Context):
        preferences = OWRecorderPreferences.from_context(context)
        if preferences.empty():
            self.report({'ERROR'}, 'plugin preferences are empty')
            return {'CANCELLED'}

        api_client = APIClient(preferences)

        ground_body_name = self.get_ground_body_name(api_client)
        if ground_body_name is None:
            self.report({'ERROR'}, 'could not get current ground body name')
            return {'CANCELLED'}

        ground_body_project_path = Path(preferences.ow_bodies_folder).joinpath(ground_body_name + '.blend')

        if not ground_body_project_path.exists():
            return_code = self._generate_ground_body_file_in_new_instance(ground_body_name)
            if not (return_code == 0 and ground_body_project_path.exists()):
                self.report({'ERROR'}, 'could not generate ground body .blend file')
                return {'CANCELLED'}

        sectors_list_text_name = f'{ground_body_name} sectors'
        if sectors_list_text_name not in bpy.data.texts:
            link_status = self._link(ground_body_project_path, 'Text', sectors_list_text_name)
            if link_status != {'FINISHED'}:
                self.report({'ERROR'}, 'could not link ground body sector list text')
                return {'CANCELLED'}

        sector_list: dict[str, int] = json.loads(bpy.data.texts[sectors_list_text_name].as_string())

        if self.sector_loading_mode == 'ALL':
            sector_indices = sector_list.values()
        else:
            current_sector_path = api_client.get_current_sector_path()
            if current_sector_path is None:
                self.report({'ERROR'}, 'could not get current sector path from API')
                return {'CANCELLED'}

            sector_indices = map(lambda p: sector_list[p], self._iter_subpaths(current_sector_path))

            if self.sector_loading_mode == 'CURRENT':
                sector_indices = (list(sector_indices)[-1],)

        sector_indices: Iterable[int] | None

        loaded_sector_collections_names: list[str] = []

        for sector_index in sector_indices:
            sector_collection_name = f'{ground_body_name} Sector #{sector_index} Collection'
            if sector_collection_name in bpy.data.collections:
                continue

            loaded_sector_collections_names.append(sector_collection_name)
            link_status = self._link(ground_body_project_path, 'Collection', sector_collection_name)
            if link_status != {'FINISHED'}:
                self.report({'ERROR'}, f'could not link {sector_collection_name}')
                return {'CANCELLED'}

        # sector_link = context.view_layer.objects.active
        # sector_link.hide_render = True

        # ground_body_collection = bpy.data.collections.new(GROUND_BODY_COLLECTION_NAME)
        # context.scene.collection.children.link(ground_body_collection)
        # ground_body_collection.objects.link(sector_link)
        # context.scene.collection.objects.unlink(sector_link)
        # ground_body_collection.hide_render = True

        if GROUND_BODY_COLLECTION_NAME not in bpy.data.collections:
            ground_body_collection = bpy.data.collections.new(GROUND_BODY_COLLECTION_NAME)
            context.scene.collection.children.link(ground_body_collection)

            ground_body_sectors_parent = bpy.data.objects.new(ground_body_name, None)
            ground_body_sectors_parent.empty_display_size = 3
            ground_body_sectors_parent.empty_display_type = 'PLAIN_AXES'
            ground_body_sectors_parent.hide_render = True

            ground_body_collection.objects.link(ground_body_sectors_parent)
        else:
            ground_body_collection = bpy.data.collections[GROUND_BODY_COLLECTION_NAME]
            ground_body_sectors_parent = ground_body_collection.objects[0]

        for loaded_sector_collection_name in loaded_sector_collections_names:
            sector_collection_instance = bpy.data.objects[loaded_sector_collection_name]
            sector_collection_instance.hide_render = True
            sector_collection_instance.hide_select = True
            sector_collection_instance.parent = ground_body_sectors_parent

            ground_body_collection.objects.link(sector_collection_instance)
            context.scene.collection.objects.unlink(sector_collection_instance)

        return {'FINISHED'}

    def _generate_ground_body_file_in_new_instance(self, ground_body_name: str) -> int:
        python_expr = f"import sys, bpy; bpy.ops.ow_recorder.generate_ground_body_background(ground_body='{ground_body_name}')"
        cmd = f'"{bpy.app.binary_path}" -noaudio --background --log-level -1 --python-expr "{python_expr}"'

        process = subprocess.run(cmd, shell=False, creationflags=subprocess.CREATE_NEW_CONSOLE)
        return process.returncode

    def _link(self, blender_project_path: Path, resource_type: str, filename: str) -> set[str]:
        return bpy.ops.wm.link(
            filename=filename,
            filepath=str(blender_project_path.joinpath(resource_type, filename)),
            directory=str(blender_project_path.joinpath(resource_type)),
        )

    def _iter_subpaths(self, path: str, separator = '/'):
        path_parts = path.split(separator)
        current_path = ''
        for path_part in path_parts:
            current_path += separator + path_part
            yield current_path[len(separator):]
