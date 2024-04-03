from math import radians
from os import path

import bpy
from bpy.path import clean_name
from bpy.types import Camera, Object, Operator
from mathutils import Euler

from ..bpy_register import bpy_register
from ..properties import CameraProperties
from ..utils import NodeBuilder, Result, add_single_prop_driver, arrange_nodes, operator_do


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
        equirect_camera = CameraProperties.of_camera(camera)

        hdri_image_path = equirect_camera.color_texture_props.absolute_recording_path
        if not path.isfile(hdri_image_path):
            Result.do_error(f'file "{equirect_camera.color_texture_props.recording_path}" not found')

        if equirect_camera.hdri_image:
            bpy.data.images.remove(equirect_camera.hdri_image, do_unlink=True)

        hdri_image = bpy.data.images.load(hdri_image_path)
        hdri_image.name = f"HDRI.{clean_name(camera.name.removeprefix('//'))}"
        equirect_camera.hdri_image = hdri_image

        if equirect_camera.hdri_node_group:
            hdri_node_group = equirect_camera.hdri_node_group
        else:
            hdri_node_group = bpy.data.node_groups.new(name=hdri_image.name, type=bpy.types.ShaderNodeTree.__name__)
            equirect_camera.hdri_node_group = hdri_node_group

        hdri_node_group.nodes.clear()

        if set(hdri_node_group.interface.items_tree.keys()) != {"Strength", "Background"}:
            hdri_node_group.interface.clear()

            strength_input = hdri_node_group.interface.new_socket(
                "Strength", socket_type=bpy.types.NodeSocketFloat.__name__, in_out="INPUT"
            )

            strength_input.default_value = 3
            strength_input.min_value = 0

            hdri_node_group.interface.new_socket(
                "Background", socket_type=bpy.types.NodeSocketShader.__name__, in_out="OUTPUT"
            )

        scene = context.scene

        def init_environment_node(node: bpy.types.ShaderNodeTexEnvironment):
            node.image = hdri_image
            image_user = node.image_user

            image_user.frame_duration = 1
            image_user.use_auto_refresh = True

            add_single_prop_driver(
                image_user,
                "frame_offset",
                target_id_type="SCENE",
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
                    input_node.set_main_output("Strength")

        arrange_nodes(hdri_node_group)

        warning_label_node = hdri_node_group.nodes.new(bpy.types.NodeReroute.__name__)
        warning_label_node.label = "This node tree is auto-generated!"
        warning_label_node.location = (75, 35)

        self.report({"INFO"}, f'node group "{hdri_node_group.name}" generated successfully')

