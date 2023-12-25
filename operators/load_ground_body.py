import json
import subprocess
from pathlib import Path
from typing import Iterable

import bpy
from bpy.props import BoolProperty, EnumProperty
from bpy.types import Context, Object, Operator

from ..api import APIClient
from ..bpy_register import bpy_register
from ..preferences import OWRecorderPreferences
from ..properties import OWRecorderReferenceProperties, OWRecorderSceneProperties
from .ground_body_selection_helper import GroundBodySelectionHelper


@bpy_register
class OW_RECORDER_OT_load_ground_body(Operator, GroundBodySelectionHelper):
    """Loads current ground body (might take a while for the first time) and links it to current project."""

    bl_idname = "ow_recorder.load_ground_body"
    bl_label = "Load ground body"

    sector_loading_mode: EnumProperty(
        name="Sector Mode",
        items=[
            ("CURRENT_AND_PARENTS", "Current and parents", ""),
            ("CURRENT", "Only current", ""),
            ("ALL", "All", "(potential high RAM usage)"),
        ],
    )

    move_ground_to_origin: BoolProperty(
        name="Move to origin on player location",
        description="Shorthand to move_ground_to_body operator",
        default=False,
    )

    def invoke(self, context: Context, _):
        reference_props = OWRecorderReferenceProperties.from_context(context)
        current_ground_body = reference_props.ground_body

        if current_ground_body is not None:
            scene_props = OWRecorderSceneProperties.from_context(context)
            self.ground_body = scene_props.ground_body_name

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: Context):
        reference_props = OWRecorderReferenceProperties.from_context(context)
        current_ground_body = reference_props.ground_body

        row = self.layout.row(align=True)
        row.enabled = current_ground_body is None
        row.label(text="Ground Body")
        row.prop(self, "ground_body", text="")

        row = self.layout.row(align=True)
        row.label(text="Sector Mode")
        row.prop(self, "sector_loading_mode", text="")

        row = self.layout.row(align=True)
        row.label(text="Move to origin on player location")
        row.prop(self, "move_ground_to_origin", text="")

    def execute(self, context: Context):
        preferences = OWRecorderPreferences.from_context(context)
        if preferences.empty():
            self.report({"ERROR"}, "plugin preferences are empty")
            return {"CANCELLED"}

        api_client = APIClient(preferences)

        ground_body_name = self.get_ground_body_name(api_client)
        if ground_body_name is None:
            self.report({"ERROR"}, "could not get current ground body name")
            return {"CANCELLED"}

        reference_props = OWRecorderReferenceProperties.from_context(context)
        scene_props = OWRecorderSceneProperties.from_context(context)
        current_ground_body: Object = reference_props.ground_body

        if current_ground_body is not None and scene_props.ground_body_name != ground_body_name:
            self.report({"ERROR"}, "multiple ground bodies in one project is not supported")
            return {"CANCELLED"}

        ground_body_project_path = Path(preferences.ow_bodies_folder).joinpath(ground_body_name + ".blend")

        if not ground_body_project_path.exists():
            return_code = self._generate_ground_body_file_in_new_instance(ground_body_name)
            if not (return_code == 0 and ground_body_project_path.exists()):
                self.report({"ERROR"}, "could not generate ground body .blend file")
                return {"CANCELLED"}

        sectors_list_text_name = f"{ground_body_name} sectors"
        if sectors_list_text_name not in bpy.data.texts:
            link_status = self._link(ground_body_project_path, "Text", sectors_list_text_name)
            if link_status != {"FINISHED"}:
                self.report({"ERROR"}, "could not link ground body sector list text")
                return {"CANCELLED"}

        sector_list: dict[str, int] = json.loads(bpy.data.texts[sectors_list_text_name].as_string())

        if self.sector_loading_mode == "ALL":
            sector_indices = sector_list.values()
        else:
            current_sectors = api_client.get_player_sectors()
            if current_sectors is None:
                self.report({"ERROR"}, "could not get current sector path from API")
                return {"CANCELLED"}

            sector_indices = map(lambda p: sector_list[p], current_sectors["sectors"])

            if self.sector_loading_mode == "CURRENT":
                sector_indices = (list(sector_indices)[-1],)

        sector_indices: Iterable[int] | None

        sector_collections_names = [
            f"{ground_body_name} Sector #{sector_index} Collection" for sector_index in sector_indices
        ]

        sector_collection_instances: list[Object] = []

        for sector_collection_name in sector_collections_names:
            if sector_collection_name in bpy.data.collections:
                continue

            link_status = self._link(ground_body_project_path, "Collection", sector_collection_name)
            if link_status != {"FINISHED"}:
                self.report({"ERROR"}, f"could not link {sector_collection_name}")
                return {"CANCELLED"}

            sector_collection_instances.append(bpy.context.active_object)

        if current_ground_body is None:
            current_ground_body = bpy.data.objects.new(ground_body_name, None)
            scene_props.ground_body_name = ground_body_name
            reference_props.ground_body = current_ground_body
            context.scene.collection.objects.link(current_ground_body)

            current_ground_body.empty_display_size = 3
            current_ground_body.empty_display_type = "PLAIN_AXES"
            current_ground_body.hide_render = True

        ground_body_hidden = current_ground_body.hide_get()

        for sector_collection_instance in sector_collection_instances:
            sector_collection_instance.instance_type = "COLLECTION"
            sector_collection_instance.empty_display_type = "PLAIN_AXES"

            sector_collection_instance.parent = current_ground_body
            sector_collection_instance.location = (0, 0, 0)
            sector_collection_instance.rotation_euler = (0, 0, 0)
            sector_collection_instance.scale = (1, 1, 1)

            sector_collection_instance.hide_render = True
            sector_collection_instance.hide_select = True
            sector_collection_instance.hide_set(state=ground_body_hidden)

        if self.move_ground_to_origin:
            context.view_layer.objects.active = None
            bpy.ops.ow_recorder.synchronize(
                sync_direction="OW_TO_BLENDER",
                ow_item="player_body",
            )
            bpy.ops.ow_recorder.move_ground_to_origin()

        return {"FINISHED"}

    def _generate_ground_body_file_in_new_instance(self, ground_body_name: str) -> int:
        python_expr = (
            f"import sys, bpy; bpy.ops.ow_recorder.generate_ground_body_background(ground_body='{ground_body_name}')"
        )
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

