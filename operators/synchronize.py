from math import radians

from bpy.props import EnumProperty
from bpy.types import Context, Object, Operator, SpaceView3D, View3DCursor
from mathutils import Matrix, Quaternion

from ..api import APIClient
from ..api.models import TransformDTO, apply_camera_dto, get_camera_dto
from ..bpy_register import bpy_register
from ..preferences import OWRecorderPreferences
from ..properties import OWRecorderReferenceProperties, OWRecorderSceneProperties


@bpy_register
class OW_RECORDER_OT_synchronize(Operator):
    """Synchronize choosen items between Blender and Outer Wilds"""

    bl_idname = "ow_recorder.synchronize"
    bl_label = "Synchronize with Outer Wilds"

    sync_direction: EnumProperty(
        name="Direction",
        items=[
            ("OW_TO_BLENDER", "Get from Outer Wilds", ""),
            ("BLENDER_TO_OW", "Send to Outer Wilds", ""),
        ],
    )

    ow_item: EnumProperty(
        name="Outer Wilds item",
        items=[
            ("free-camera", "Free camera", ""),
            ("player/body", "Player body", ""),
            (
                "player/camera",
                "Player camera",
                "(modifying Player camera is not allowed!)",
            ),
        ],
    )

    @classmethod
    def poll(cls, context) -> bool:
        reference_props = OWRecorderReferenceProperties.from_context(context)
        return reference_props.ground_body is not None

    def invoke(self, context: Context, _):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, _: Context):
        self.layout.prop(self, "sync_direction", expand=True)

        row = self.layout.row(align=True)
        # row.label(text='Outer Wilds item')
        row.prop(self, "ow_item", expand=True)

    def execute(self, context: Context):
        if self.sync_direction == "OW_TO_BLENDER":
            return self._sync_ow_to_blender(context)
        elif self.sync_direction == "BLENDER_TO_OW":
            return self._sync_blender_to_ow(context)

        self.report({"ERROR"}, "unsupported direction")
        return {"CANCELLED"}

    def _sync_ow_to_blender(self, context: Context):
        scene_props = OWRecorderSceneProperties.from_context(context)
        reference_props = OWRecorderReferenceProperties.from_context(context)
        api_client = APIClient(OWRecorderPreferences.from_context(context))
        ground_body: Object = reference_props.ground_body

        blender_item = self._get_blender_item(context)

        transforms = api_client.get_transform(self.ow_item, local_to=scene_props.ground_body_name)
        if transforms is None:
            self.report({"ERROR"}, "failed to get transform from Outer Wilds")
            return {"CANCELLED"}

        _, new_transform = transforms

        if isinstance(blender_item, Object):
            blender_item.matrix_parent_inverse = Matrix.Identity(4)

        new_transform = new_transform.unity_to_blender()

        new_matrix: Matrix = ground_body.matrix_world @ Matrix.LocRotScale(
            new_transform.position,
            new_transform.rotation @ Quaternion((0, 1, 0), radians(180)),
            new_transform.scale,
        )

        new_location, new_rotation, new_scale = new_matrix.decompose()
        blender_item.location = new_location

        blender_item.rotation_mode = "QUATERNION"
        blender_item.rotation_quaternion = new_rotation
        if isinstance(blender_item, Object):
            blender_item.scale = new_scale
            if blender_item.type != "CAMERA":
                blender_item.rotation_quaternion @= Quaternion((1, 0, 0), radians(-90))
                blender_item.rotation_quaternion @= Quaternion((0, 0, 1), radians(180))
        else:
            blender_item.matrix @= Matrix.Rotation(radians(-90), 4, (1, 0, 0))

        if isinstance(blender_item, Object) and blender_item.type == "CAMERA" and ("camera" in self.ow_item):
            camera_info = api_client.get_camera_info(self.ow_item)
            if camera_info is None:
                self.report({"ERROR"}, "failed to get camera info from Outer Wilds")
                return {"CANCELLED"}

            apply_camera_dto(blender_item.data, camera_info)

        return {"FINISHED"}

    def _sync_blender_to_ow(self, context: Context):
        if self.ow_item == "player/camera":
            self.report({"INFO"}, "modifying Player Camera is not allowed")
            return {"CANCELLED"}

        scene_props = OWRecorderSceneProperties.from_context(context)
        reference_props = OWRecorderReferenceProperties.from_context(context)
        api_client = APIClient(OWRecorderPreferences.from_context(context))
        ground_body: Object = reference_props.ground_body

        blender_item = self._get_blender_item(context)

        if isinstance(blender_item, Object):
            blender_item_matrix = blender_item.matrix_world
        else:
            blender_item_matrix = blender_item.matrix

        new_transform = ground_body.matrix_world.inverted() @ blender_item_matrix
        new_transform = TransformDTO.from_matrix(new_transform)
        new_transform = new_transform.blender_to_unity()

        success = api_client.set_transform(self.ow_item, new_transform, local_to=scene_props.ground_body_name)
        if not success:
            self.report({"INFO"}, "failed to set transform in Outer Wilds")
            return {"CANCELLED"}

        if isinstance(blender_item, Object) and blender_item.type == "CAMERA" and ("camera" in self.ow_item):
            new_camera_info = get_camera_dto(blender_item.data)
            success = api_client.set_camera_info(self.ow_item, new_camera_info)
            if not success:
                self.report({"INFO"}, "failed to set camera info in Outer Wilds")
                return {"CANCELLED"}

        return {"FINISHED"}

    def _get_blender_item(self, context: Context) -> Object | View3DCursor:
        space: SpaceView3D = context.space_data
        if context.scene.camera and space.region_3d.view_perspective == "CAMERA":
            return context.scene.camera

        selected_objects = context.view_layer.objects.selected
        return selected_objects[0] if len(selected_objects) > 0 else context.scene.cursor

