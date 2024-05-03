from collections import Counter
from math import radians
from pathlib import Path

import bpy
from bpy.props import StringProperty
from bpy.types import Object, Operator
from mathutils import Matrix

from ..api import APIClient, Transform
from ..bpy_register import bpy_register
from ..properties import OuterScoutPreferences
from ..utils import get_child_by_path, iter_parents, operator_do


@bpy_register
class GenerateBodyOperator(Operator):
    """Generate Outer Wilds body .blend from extracted .fbx"""

    bl_idname = "outer_scout.generate_body"
    bl_label = "Generate ground body"

    body_name: StringProperty(name="Ground Body")

    @operator_do
    def execute(self, context):
        preferences = OuterScoutPreferences.from_context(context)
        if not preferences.has_file_paths:
            self._log("ERROR", "addon preferences are not valid")
            return {"CANCELLED"}

        ow_assets_folder, ow_bodies_folder = map(Path, (preferences.ow_assets_folder, preferences.ow_bodies_folder))

        body_name = self.body_name
        body_name_abbr = self._body_name_abbreviation(body_name)

        body_fbx_path = ow_bodies_folder.joinpath(body_name + ".fbx")
        if not body_fbx_path.is_file():
            self._log("ERROR", f"{body_fbx_path} not found. Export it using asset extractor")
            return {"CANCELLED"}

        self._log("INFO", f"generating {body_name} object...")
        self._log("INFO", f"fetching {body_name} assets list")

        api_client = APIClient.from_context(context)
        body_mesh_json = api_client.get_object_mesh(
            body_name,
            ignore_paths=list(map(lambda i: i.name, preferences.import_ignore_paths)),
            ignore_layers=list(map(lambda i: i.name, preferences.import_ignore_layers)),
            case_sensitive=False,
        ).then()

        streamed_asset_paths = Counter(
            streamed_mesh["path"] for sector in body_mesh_json["sectors"] for streamed_mesh in sector["streamedMeshes"]
        )

        imported_objs: dict[str, tuple[Object | None, int]] = {
            asset_path: (None, asset_uses_count) for asset_path, asset_uses_count in streamed_asset_paths.items()
        }

        self._log("INFO", f"importing {len(imported_objs)} .obj files of streamed assets")

        for asset_path, (_, asset_uses_count) in imported_objs.items():
            try:
                obj_path = str(ow_assets_folder.joinpath(asset_path.removesuffix(".asset") + ".obj"))
                bpy.ops.wm.obj_import(filepath=obj_path)
            except:
                self._log("WARNING", f"failed to import .obj file at {obj_path}")
                continue

            imported_obj = bpy.data.objects[context.view_layer.objects.active.name]
            if imported_obj.type != "EMPTY":
                imported_objs[asset_path] = (imported_obj, asset_uses_count)

        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.transform_apply()
        bpy.ops.object.select_all(action="DESELECT")

        body_fbx_path = str(body_fbx_path)
        self._log("INFO", f"importing {body_fbx_path}")
        fbx_import_result = bpy.ops.import_scene.fbx(filepath=body_fbx_path)
        if fbx_import_result != {"FINISHED"}:
            self._log("ERROR", f"failed to import ground body fbx: {body_fbx_path}")
            return {"CANCELLED"}

        fbx_body_object = bpy.data.objects[body_name]
        fbx_body_object.name += "_fbx"

        self._log("INFO", f"deleting {body_name} parents")
        bpy.data.batch_remove(list(iter_parents(fbx_body_object)))

        self._log("INFO", f"clearing {len(bpy.data.materials)} materials")
        bpy.data.batch_remove(bpy.data.materials)

        self._log("INFO", f"clearing {len(bpy.data.images)} images")
        bpy.data.batch_remove(bpy.data.images)

        self._log("INFO", "loading sectors")
        sectors_count = len(body_mesh_json["sectors"])

        body_collection = bpy.data.collections.new(body_name)
        context.scene.collection.children.link(body_collection)

        sector_indices_text = bpy.data.texts.new(f"{body_name} sectors")
        sector_indices_text.use_fake_user = True

        sector_indices_text.write("{\n")

        identity_transform = Matrix.Identity(4)

        # TODO: something to do with importing options...
        add_transform_plain = Matrix.Rotation(radians(180), 4, "Z") @ Matrix.Rotation(radians(90), 4, "X")
        add_transform_streamed = Matrix.Rotation(radians(180), 4, "Z")

        for sector_index, sector_info in enumerate(body_mesh_json["sectors"]):
            sector_path = sector_info["path"].removeprefix(body_mesh_json["body"]["path"]).removeprefix("/")
            self._log("INFO", f"* sector '{sector_path}' [{sector_index + 1}/{sectors_count}]")

            sector_indices_text.write(f'    "{sector_path}": {sector_index}')
            if (sector_index + 1) < sectors_count:
                sector_indices_text.write(",")
            sector_indices_text.write("\n")

            sector_collection = bpy.data.collections.new(f"{body_name}.Sector.{sector_index}")

            body_collection.children.link(sector_collection)

            self._log("INFO", f'placing plain meshes ({len(sector_info["plainMeshes"])} objects)')

            for plain_mesh_json in sector_info["plainMeshes"]:
                mesh_path = plain_mesh_json["path"].split("/")[1:]

                fbx_child = get_child_by_path(fbx_body_object, mesh_path, mask_duplicates=True)
                if fbx_child is None:
                    self._log("WARNING", f'missing plain mesh child at {plain_mesh_json["path"]}')
                    continue

                context.collection.objects.unlink(fbx_child)
                sector_collection.objects.link(fbx_child)

                fbx_child.name = f"{body_name_abbr}.{fbx_child.name}"
                if fbx_child.data and fbx_child.data.id_type == "MESH":
                    fbx_child.data.name = fbx_child.name

                unity_transform = Transform.from_json(plain_mesh_json["transform"])
                fbx_child["unity_path"] = plain_mesh_json["path"]
                fbx_child["unity_is_streamed"] = False

                fbx_child.parent = None
                fbx_child.matrix_parent_inverse = identity_transform
                fbx_child.matrix_world = unity_transform.to_right_matrix() @ add_transform_plain

            self._log("INFO", f'placing streamed meshes ({len(sector_info["streamedMeshes"])} objects)')

            for streamed_mesh_json in sector_info["streamedMeshes"]:
                asset_path = streamed_mesh_json["path"]
                if asset_path not in imported_objs:
                    continue

                imported_obj, asset_uses_count = imported_objs[asset_path]
                if imported_obj is None:
                    continue

                obj_copy = imported_obj.copy()
                sector_collection.objects.link(obj_copy)

                asset_uses_count -= 1
                if asset_uses_count <= 0:
                    bpy.data.objects.remove(imported_obj, do_unlink=True)
                    imported_objs[asset_path] = (None, 0)
                else:
                    imported_objs[asset_path] = (imported_obj, asset_uses_count)

                obj_copy.name = f"{body_name_abbr}.{obj_copy.name}"
                if obj_copy.data and obj_copy.data.id_type == "MESH":
                    obj_copy.data.name = obj_copy.name

                unity_transform = Transform.from_json(streamed_mesh_json["transform"])
                obj_copy["unity_path"] = asset_path
                obj_copy["unity_is_streamed"] = True

                obj_copy.parent = None
                obj_copy.matrix_parent_inverse = identity_transform
                obj_copy.matrix_world = unity_transform.to_right_matrix() @ add_transform_streamed

            self._log("INFO", "deleting empties")
            bpy.data.batch_remove([e for e in sector_collection.objects if e.type == "EMPTY"])

        sector_indices_text.write("}")

        objects_to_delete = context.scene.collection.objects
        num_of_objects_to_delete = len(objects_to_delete)
        self._log("INFO", f"deleting {num_of_objects_to_delete} scene objects")
        bpy.data.batch_remove(objects_to_delete)

        self._log("INFO", "finished")
        bpy.ops.object.select_all(action="DESELECT")

    def _body_name_abbreviation(self, ground_body_name: str) -> str:
        ground_body_name = ground_body_name.removesuffix("_Body")
        return "".join(ch for ch in ground_body_name if ch.isupper())

    def _log(self, type: str, message: str):
        print(f"[{type}] {message}")
        # reports don't appear dynamically in console window
        # self.report({type}, message)

