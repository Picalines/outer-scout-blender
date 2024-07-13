from math import radians

from bpy.props import EnumProperty
from bpy.types import Camera, Context, Object, Operator, SpaceView3D, View3DCursor
from mathutils import Matrix, Quaternion

from ..api import APIClient, PerspectiveJson, Transform
from ..bpy_register import bpy_register
from ..properties import SceneProperties
from ..utils import Result, operator_do


@bpy_register
class SynchronizeOperator(Operator):
    """Synchronize choosen items between Blender and Outer Wilds"""

    bl_idname = "outer_scout.synchronize"
    bl_label = "Synchronize with Outer Wilds"

    sync_direction: EnumProperty(
        name="Direction",
        items=[
            ("OW_TO_BLENDER", "Get from Outer Wilds", "Copies object/camera data from Outer Wilds to Blender"),
            ("BLENDER_TO_OW", "Send to Outer Wilds", "Copies object/camera data from Blender to Outer Wilds"),
        ],
    )

    ow_item: EnumProperty(
        name="Outer Wilds item",
        items=[
            (
                "ACTIVE_CAMERA",
                "Active Camera",
                "If possible, the camera perspective will be matched\n\nNote: player camera cannot be modified",
            ),
            ("PLAYER_BODY", "Player Body", ""),
            ("SURVEYOR_PROBE", "Scout", "Note: scout cannot be moved"),
        ],
    )

    def invoke(self, context: Context, _):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, _: Context):
        layout = self.layout

        layout.prop(self, "sync_direction", expand=True)
        layout.prop(self, "ow_item", expand=True)

    @operator_do
    def execute(self, context: Context):
        if self.sync_direction == "OW_TO_BLENDER":
            return self._sync_ow_to_blender(context).then()
        elif self.sync_direction == "BLENDER_TO_OW":
            return self._sync_blender_to_ow(context).then()

        raise NotImplementedError()

    @Result.do()
    def _sync_ow_to_blender(self, context: Context):
        scene_props = SceneProperties.from_context(context)
        api_client = APIClient.from_context(context)

        blender_item = self._get_blender_item(context)

        ow_object_name = self._get_ow_object_name(api_client).then()
        ow_object = api_client.get_object(ow_object_name, origin=scene_props.origin_parent).then()

        should_sync_perspective = (
            isinstance(blender_item, Object) and blender_item.type == "CAMERA" and self.ow_item == "ACTIVE_CAMERA"
        )

        if should_sync_perspective:
            ow_camera = api_client.get_camera(ow_object_name).then()
            ow_perspective = ow_camera["perspective"] if "perspective" in ow_camera else None
            if ow_perspective is None:
                self.report({"WARNING"}, "camera perspective wasn't synced. Try to send your data first")
        else:
            ow_perspective = None

        new_transform = Transform.from_json(ow_object["transform"]).to_right()

        if isinstance(blender_item, Object):
            blender_item.matrix_parent_inverse = Matrix.Identity(4)

        ground_body: Object | None = scene_props.ground_body
        ground_matrix = ground_body.matrix_world if ground_body is not None else Matrix.Identity(4)
        new_matrix: Matrix = ground_matrix @ new_transform.to_matrix()

        new_location, new_rotation, new_scale = new_matrix.decompose()
        blender_item.location = new_location

        blender_item.rotation_mode = "QUATERNION"
        blender_item.rotation_quaternion = new_rotation
        if isinstance(blender_item, Object):
            blender_item.scale = new_scale
            if blender_item.type == "CAMERA":
                blender_item.rotation_quaternion @= Quaternion((1, 0, 0), radians(90))
            else:
                if self.ow_item == "SURVEYOR_PROBE":
                    blender_item.rotation_quaternion @= Quaternion((1, 0, 0), radians(90))

                blender_item.rotation_quaternion @= Quaternion((0, 0, 1), radians(180))

        if ow_perspective is not None:
            blender_camera: Camera = blender_item.data
            blender_camera.type = "PERSP"
            blender_camera.lens_unit = "MILLIMETERS"
            blender_camera.lens = ow_perspective["focalLength"]
            blender_camera.sensor_width = ow_perspective["sensorSize"][0]
            blender_camera.sensor_height = ow_perspective["sensorSize"][1]
            blender_camera.shift_x = ow_perspective["lensShift"][0]
            blender_camera.shift_y = ow_perspective["lensShift"][1]
            blender_camera.clip_start = ow_perspective["nearClipPlane"]
            blender_camera.clip_end = ow_perspective["farClipPlane"]

            render_settings = context.scene.render
            res_x, res_y = render_settings.resolution_x, render_settings.resolution_y
            blender_camera.sensor_fit = "HORIZONTAL" if res_x >= res_y else "VERTICAL"

        return {"FINISHED"}

    @Result.do()
    def _sync_blender_to_ow(self, context: Context):
        scene_props = SceneProperties.from_context(context)
        api_client = APIClient.from_context(context)

        ow_object_name = self._get_ow_object_name(api_client).then()
        if ow_object_name == "PlayerCamera":
            Result.do_error("player camera cannot be modified")
        elif ow_object_name == "Probe_Body":
            Result.do_error("scout cannot be moved")

        blender_item = self._get_blender_item(context)
        blender_item_matrix = blender_item.matrix_world if isinstance(blender_item, Object) else blender_item.matrix

        ground_body: Object | None = scene_props.ground_body
        ground_matrix = ground_body.matrix_world if ground_body is not None else Matrix.Identity(4)
        new_matrix = ground_matrix.inverted() @ blender_item_matrix

        if blender_item.type == "CAMERA":
            new_matrix @= Matrix.Rotation(radians(-90), 4, "X")
        else:
            new_matrix @= Matrix.Rotation(radians(180), 4, "Z")

        new_transform = Transform.from_matrix(new_matrix).to_left()

        api_client.put_object(name=ow_object_name, transform=new_transform, origin=scene_props.origin_parent).then()

        if isinstance(blender_item, Object) and blender_item.type == "CAMERA" and self.ow_item == "ACTIVE_CAMERA":
            blender_camera: Camera = blender_item.data
            new_perspective: PerspectiveJson = {
                "focalLength": blender_camera.lens,
                "sensorSize": (blender_camera.sensor_width, blender_camera.sensor_height),
                "lensShift": (blender_camera.shift_x, blender_camera.shift_y),
                "nearClipPlane": blender_camera.clip_start,
                "farClipPlane": blender_camera.clip_end,
            }

            api_client.put_camera(object_name=ow_object_name, perspective=new_perspective).then()

        return {"FINISHED"}

    @Result.do()
    def _get_ow_object_name(self, api_client: APIClient) -> str:
        match self.ow_item:
            case "ACTIVE_CAMERA":
                return api_client.get_active_camera().then()["name"]
            case "PLAYER_BODY":
                return "Player_Body"
            case "SURVEYOR_PROBE":
                return "Probe_Body"

        raise NotImplementedError()

    def _get_blender_item(self, context: Context) -> Object | View3DCursor:
        space: SpaceView3D = context.space_data
        if context.scene.camera and space.region_3d.view_perspective == "CAMERA":
            return context.scene.camera

        selected_objects = context.view_layer.objects.selected
        return selected_objects[0] if len(selected_objects) > 0 else context.scene.cursor
