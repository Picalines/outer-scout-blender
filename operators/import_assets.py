import bpy
from bpy.types import Operator

from ..bpy_register import bpy_register
from ..properties import CameraProperties, SceneProperties
from ..utils import operator_do


@bpy_register
class ImportAssetsOperator(Operator):
    """Imports all assets created/recorded by Outer Scout"""

    bl_idname = "outer_scout.import_assets"
    bl_label = "Import Assets"

    @classmethod
    def poll(cls, context) -> bool:
        scene_props = SceneProperties.from_context(context)
        return scene_props.is_scene_created

    @operator_do
    def execute(self, context):
        scene = context.scene

        for camera_object, camera in [
            (camera_obj, camera_obj.data) for camera_obj in scene.objects if camera_obj.type == "CAMERA"
        ]:
            camera_props = CameraProperties.of_camera(camera)
            if not camera_props.is_active:
                continue

            with context.temp_override(active_object=camera_object):
                bpy.ops.outer_scout.import_camera_recording()
                if camera_props.hdri_node_group:
                    bpy.ops.outer_scout.generate_hdri_nodes()

        scene_props = SceneProperties.from_context(context)
        if scene_props.compositor_node_group:
            bpy.ops.outer_scout.generate_compositor_nodes()

