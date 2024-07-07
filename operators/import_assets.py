import bpy
from bpy.types import Camera, Object, Operator

from ..bpy_register import bpy_register
from ..properties import CameraProperties, ObjectProperties, SceneProperties
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

        for object in scene.objects:
            object: Object

            object_props = ObjectProperties.of_object(object)
            if not object_props.has_unity_object_name:
                continue

            match object.type:
                case "CAMERA":
                    camera: Camera = object.data
                    camera_props = CameraProperties.of_camera(camera)
                    if not camera_props.is_active:
                        continue

                    with context.temp_override(active_object=object):
                        bpy.ops.outer_scout.import_camera_recording()
                        if camera_props.hdri_node_group:
                            bpy.ops.outer_scout.generate_hdri_nodes()
                case _:
                    transform_props = object_props.transform_props

                    if transform_props.has_recording_path and transform_props.mode == "RECORD":
                        with context.temp_override(active_object=object):
                            bpy.ops.outer_scout.import_transform_recording()

                        if transform_props.record_once:
                            transform_props.mode = "APPLY"

        scene_props = SceneProperties.from_context(context)
        if scene_props.compositor_node_group:
            bpy.ops.outer_scout.generate_compositor_nodes()
