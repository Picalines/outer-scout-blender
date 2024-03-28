import json
import subprocess
from pathlib import Path
from typing import Iterable

import bpy
from bpy.props import EnumProperty
from bpy.types import Object, Operator

from ..api import APIClient
from ..bpy_register import bpy_register
from ..operators import GenerateBodyBackgroundOperator
from ..properties import OuterScoutPreferences, SceneProperties
from ..utils import Result, operator_do


@bpy_register
class ImportBodyOperator(Operator):
    """Loads current ground body (might take a while for the first time) and links it to current project"""

    bl_idname = "outer_scout.import_body"
    bl_label = "Import Ground Body"

    sector_loading_mode: EnumProperty(
        name="Sector Import Mode",
        items=[
            ("CURRENT_AND_PARENTS", "Current and parents", ""),
            ("CURRENT", "Only current", ""),
            ("ALL", "All", ""),
        ],
    )

    @classmethod
    def poll(cls, context) -> bool:
        scene_props = SceneProperties.from_context(context)
        return scene_props.has_origin and not scene_props.has_ground_body

    def invoke(self, context, _):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, _):
        layout = self.layout
        layout.use_property_split = True

        layout.prop(self, "sector_loading_mode")

    @operator_do
    def execute(self, context):
        preferences = OuterScoutPreferences.from_context(context)
        if not preferences.are_valid:
            # TODO: call operator to fill preferences?
            Result.do_error("plugin preferences are not valid")

        scene_props = SceneProperties.from_context(context)
        api_client = APIClient.from_context(context)

        body_name = scene_props.origin_parent

        body_project_path = Path(preferences.ow_bodies_folder).joinpath(body_name + ".blend")

        if not body_project_path.exists():
            # TODO: make button in preferences menu?
            return_code = self._generate_body_in_background(body_name)
            if not (return_code == 0 and body_project_path.exists()):
                Result.do_error("could not generate body .blend file")

        sectors_list_text_name = f"{body_name} sectors"
        if sectors_list_text_name not in bpy.data.texts:
            link_status = self._link(body_project_path, "Text", sectors_list_text_name)
            if link_status != {"FINISHED"}:
                Result.do_error("could not link body sector list text")

        sector_list: dict[str, int] = json.loads(bpy.data.texts[sectors_list_text_name].as_string())

        if self.sector_loading_mode == "ALL":
            sector_indices = sector_list.values()
        else:
            player_sectors = api_client.get_player_sectors().then()

            sector_indices = (
                sector_index
                for sector_path, sector_index in sector_list.items()
                if sector_path in player_sectors["lastEntered"]
            )

            if self.sector_loading_mode == "CURRENT":
                sector_indices = (list(sector_indices)[-1],)

        sector_indices: Iterable[int] | None
        sector_collections_names = [f"{body_name}.Sector.{sector_index}" for sector_index in sector_indices]
        sector_collection_instances: list[Object] = []

        for sector_collection_name in sector_collections_names:
            if sector_collection_name in bpy.data.collections:
                continue

            link_status = self._link(body_project_path, "Collection", sector_collection_name)
            if link_status != {"FINISHED"}:
                Result.do_error(f"could not link {sector_collection_name}")

            sector_collection_instances.append(bpy.context.active_object)

        body_object = bpy.data.objects.new(body_name, None)
        scene_props.ground_body = body_object
        context.scene.collection.objects.link(body_object)

        body_object.empty_display_size = 3
        body_object.empty_display_type = "PLAIN_AXES"
        body_object.hide_render = True
        body_object.lock_location = (True,) * 3
        body_object.lock_rotation = (True,) * 3
        body_object.lock_scale = (True,) * 3

        is_body_hidden = body_object.hide_get()

        for sector_collection_instance in sector_collection_instances:
            sector_collection_instance.instance_type = "COLLECTION"
            sector_collection_instance.empty_display_type = "PLAIN_AXES"

            sector_collection_instance.parent = body_object
            sector_collection_instance.location = (0, 0, 0)
            sector_collection_instance.rotation_euler = (0, 0, 0)
            sector_collection_instance.scale = (1, 1, 1)

            sector_collection_instance.users_collection[0].objects.unlink(sector_collection_instance)
            context.scene.collection.objects.link(sector_collection_instance)

            sector_collection_instance.hide_render = True
            sector_collection_instance.hide_select = True
            sector_collection_instance.hide_set(state=is_body_hidden)

        bpy.ops.outer_scout.align_ground_body()

    def _generate_body_in_background(self, body_name: str) -> int:
        operator = GenerateBodyBackgroundOperator.bl_idname
        python_expr = f"import sys, bpy; bpy.ops.{operator}(body_name='{body_name}')"
        cmd = f'"{bpy.app.binary_path}" -noaudio --background --log-level -1 --python-expr "{python_expr}"'

        process = subprocess.run(cmd, shell=False, creationflags=subprocess.CREATE_NEW_CONSOLE)
        return process.returncode

    def _link(self, blender_project_path: Path, resource_type: str, filename: str) -> set[str]:
        return bpy.ops.wm.link(
            filename=filename,
            filepath=str(blender_project_path.joinpath(resource_type, filename)),
            directory=str(blender_project_path.joinpath(resource_type)),
            active_collection=True,
            autoselect=True,
            instance_collections=True,
        )

