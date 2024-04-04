from math import radians
from os import path

import bpy
from bpy.path import clean_name
from bpy.types import Camera, Image, Object, Operator
from mathutils import Euler

from ..bpy_register import bpy_register
from ..properties import CameraProperties
from ..utils import NodeBuilder, NodeTreeInterfaceBuilder, Result, add_single_prop_driver, arrange_nodes, operator_do


@bpy_register
class GenerateHDRINodesOperator(Operator):
    """Generates HDRI node group for the Outer Scout camera"""

    bl_idname = "outer_scout.generate_hdri_nodes"
    bl_label = "Generate HDRI nodes"

    @classmethod
    def poll(cls, context) -> bool:
        active_object: Object = context.active_object
        if not active_object or active_object.type != "CAMERA":
            return False

        camera_props = CameraProperties.of_camera(active_object.data)
        return (
            camera_props.outer_scout_type == "EQUIRECTANGULAR" and camera_props.color_texture_props.has_recording_path
        )

    @operator_do
    def execute(self, context):
        camera: Camera = context.active_object.data

        hdri_image = self._import_hdri_image(camera).then()

        equirect_camera = CameraProperties.of_camera(camera)
        if equirect_camera.hdri_node_group:
            hdri_node_group = equirect_camera.hdri_node_group
        else:
            hdri_node_group = bpy.data.node_groups.new(name=hdri_image.name, type=bpy.types.ShaderNodeTree.__name__)
            equirect_camera.hdri_node_group = hdri_node_group

        hdri_node_group.nodes.clear()

        STRENGTH_IN_NAME = "Strength"
        BACKGROUND_OUT_NAME = "Background"

        with NodeTreeInterfaceBuilder(hdri_node_group.interface) as interface_builder:
            interface_builder.add_input(STRENGTH_IN_NAME, bpy.types.NodeSocketFloat, min_value=0, default_value=3)
            interface_builder.add_output(BACKGROUND_OUT_NAME, bpy.types.NodeSocketShader)

        scene = context.scene

        def init_environment_node(node: bpy.types.ShaderNodeTexEnvironment):
            node.image = hdri_image
            image_user = node.image_user

            image_user.frame_duration = 1
            image_user.use_auto_refresh = True

            add_single_prop_driver(
                image_user,
                "frame_offset",
                target_id=scene,
                target_data_path="frame_start",
                var_name="frame_start",
                expression="frame - frame_start",
            )

        with NodeBuilder(hdri_node_group, bpy.types.NodeGroupOutput) as output_node:
            with output_node.build_input(0, bpy.types.ShaderNodeBackground) as background_node:
                with background_node.build_input("Color", bpy.types.ShaderNodeTexEnvironment) as environment_node:
                    environment_node.defer_init(init_environment_node)

                    with environment_node.build_input("Vector", bpy.types.ShaderNodeMapping) as mapping_node:
                        mapping_node.set_input_value("Rotation", Euler((0, 0, radians(-90))))

                        with mapping_node.build_input("Vector", bpy.types.ShaderNodeTexCoord) as texture_coord_node:
                            texture_coord_node.set_main_output("Generated")

                with background_node.build_input("Strength", bpy.types.NodeGroupInput) as input_node:
                    input_node.set_main_output(STRENGTH_IN_NAME)

        arrange_nodes(hdri_node_group)

        warning_label_node = hdri_node_group.nodes.new(bpy.types.NodeReroute.__name__)
        warning_label_node.label = "This node tree is auto-generated!"
        warning_label_node.location = (75, 35)

        self.report({"INFO"}, f'node group "{hdri_node_group.name}" generated successfully')

    @Result.do()
    def _import_hdri_image(self, camera: Camera) -> Image:
        camera_props = CameraProperties.of_camera(camera)

        hdri_image_path = camera_props.color_texture_props.absolute_recording_path
        if not path.isfile(hdri_image_path):
            Result.do_error(f'file "{camera_props.color_texture_props.recording_path}" not found')

        old_hdri_image: Image = camera_props.hdri_image
        new_hdri_image = bpy.data.images.load(hdri_image_path)

        if old_hdri_image is not None:
            old_name = old_hdri_image.name
            old_hdri_image.user_remap(new_hdri_image)
            bpy.data.images.remove(old_hdri_image)
            new_hdri_image.name = old_name
        else:
            new_hdri_image.name = f"HDRI.{clean_name(camera.name.removeprefix('//'))}"

        camera_props.hdri_image = new_hdri_image

        return new_hdri_image

