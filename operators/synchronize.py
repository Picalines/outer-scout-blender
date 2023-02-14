from math import radians
from mathutils import Quaternion, Matrix

import bpy
from bpy.types import Operator, Context, Object, View3DCursor
from bpy.props import EnumProperty

from ..bpy_register import bpy_register
from ..ow_objects import get_current_ground_body, get_current_hdri_pivot
from ..preferences import OWRecorderPreferences
from ..api import APIClient
from ..api.models import TransformModel, apply_camera_info, camera_info_from_blender


@bpy_register
class OW_RECORDER_OT_synchronize(Operator):
    '''Synchronize choosen items between Blender and Outer Wilds'''

    bl_idname = 'ow_recorder.synchronize'
    bl_label = 'Synchronize with Outer Wilds'

    sync_direction: EnumProperty(
        name='Direction',
        items=[
            ('OW_TO_BLENDER', 'Outer Wilds to Blender', ''),
            ('BLENDER_TO_OW', 'Blender to Outer Wilds', ''),
        ],
    )

    blender_item: EnumProperty(
        name='Blender item',
        items=[
            ('CURSOR', 'Cursor', ''),
            ('CAMERA', 'Camera', ''),
            ('HDRI_PIVOT', 'HDRI pivot', ''),
        ],
    )

    ow_item: EnumProperty(
        name='Outer Wilds item',
        items=[
            ('free_camera', 'Free camera', ''),
            ('player/body', 'Player body', ''),
            ('player/camera', 'Player camera', '(modifying Player camera is not allowed!)'),
        ]
    )

    @classmethod
    def poll(cls, _) -> bool:
        return get_current_ground_body() is not None

    def invoke(self, context: Context, _):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: Context):
        self._add_blender_items(context)

        if self.sync_direction == 'OW_TO_BLENDER':
            return self._sync_ow_to_blender(context)
        elif self.sync_direction == 'BLENDER_TO_OW':
            return self._sync_blender_to_ow(context)

        self.report({'ERROR'}, 'unsupported direction')
        return {'CANCELLED'}

    def _sync_ow_to_blender(self, context: Context):
        api_cilent = APIClient(OWRecorderPreferences.from_context(context))
        ground_body: Object = get_current_ground_body()

        blender_item = self._get_blender_item(context)

        new_transform = api_cilent.get_transform_local_to_ground_body(self.ow_item)
        if new_transform is None:
            self.report({'ERROR'}, 'failed to get transform from Outer Wilds')
            return {'CANCELLED'}

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
        blender_item.rotation_mode = 'QUATERNION'
        blender_item.rotation_quaternion = new_rotation
        if self.blender_item != 'CURSOR':
            blender_item.scale = new_scale
        else:
            blender_item.matrix @= Matrix.Rotation(radians(-90), 4, (1, 0, 0))

        if self.blender_item == 'CAMERA' and ('camera' in self.ow_item):
            camera_info = api_cilent.get_camera_info(self.ow_item)
            if camera_info is None:
                self.report({'ERROR'}, 'failed to get camera info from Outer Wilds')
                return {'CANCELLED'}

            apply_camera_info(context.scene.camera.data, camera_info)

        return {'FINISHED'}

    def _sync_blender_to_ow(self, context: Context):
        if self.ow_item == 'player/camera':
            self.report({'INFO'}, 'modifying Player Camera is not allowed')
            return {'CANCELLED'}

        api_cilent = APIClient(OWRecorderPreferences.from_context(context))
        ground_body: Object = get_current_ground_body()

        blender_item = self._get_blender_item(context)

        if isinstance(blender_item, Object):
            blender_item_matrix = blender_item.matrix_world
        else:
            blender_item_matrix = blender_item.matrix

        new_transform_local_to_ground_body = ground_body.matrix_world.inverted() @ blender_item_matrix
        new_transform_local_to_ground_body = TransformModel.from_matrix(new_transform_local_to_ground_body)
        new_transform_local_to_ground_body = new_transform_local_to_ground_body.blender_to_unity()

        success = api_cilent.set_transform_local_to_ground_body(self.ow_item, new_transform_local_to_ground_body)
        if success is False:
            self.report({'INFO'}, 'failed to set transform in Outer Wilds')
            return {'CANCELLED'}

        if self.blender_item == 'CAMERA' and ('camera' in self.ow_item):
            new_camera_info = camera_info_from_blender(context.scene.camera.data)
            success = api_cilent.set_camera_info(self.ow_item, new_camera_info)
            if success is False:
                self.report({'INFO'}, 'failed to set camera info in Outer Wilds')
                return {'CANCELLED'}

        return {'FINISHED'}

    def _get_blender_item(self, context: Context) -> Object | View3DCursor:
        if self.blender_item == 'HDRI_PIVOT':
            return get_current_hdri_pivot()

        return getattr(context.scene, self.blender_item.lower())

    def _add_blender_items(self, context: Context):
        if self.blender_item == 'CAMERA':
            if context.scene.camera is None:
                bpy.ops.object.camera_add(context)

        elif '_PIVOT' in self.blender_item:
            bpy.ops.ow_recorder.create_ow_pivots(context)
