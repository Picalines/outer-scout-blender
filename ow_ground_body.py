import os
from mathutils import Quaternion
from math import radians

import bpy
from bpy.types import Object

from .preferences import OWSceneImporterPreferences
from .ow_scene_data import OWSceneData, apply_transform_data


def load_ground_body(ow_data: OWSceneData, preferences: OWSceneImporterPreferences) -> Object | None:
    ow_body_name = ow_data['ground_body']['name']

    ow_body_project_path = os.path.join(preferences.ow_bodies_folder, ow_body_name + '.blend')
    ow_body_project_import_status = bpy.ops.wm.link(
        filepath=os.path.join(ow_body_project_path, 'Collection', 'Collection'),
        filename='Collection',
        directory=os.path.join(ow_body_project_path, 'Collection'))

    if ow_body_project_import_status != {'FINISHED'}:
        return None

    ow_body_link = bpy.context.active_object
    ow_body_link.name = ow_body_name
    ow_body_link.hide_render = True

    apply_transform_data(ow_body_link, ow_data['ground_body']['transform'])
    ow_body_link.rotation_quaternion @= Quaternion((0, 1, 0), radians(90))

    return ow_body_link
