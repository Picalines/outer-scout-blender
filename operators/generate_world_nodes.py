from mathutils import Euler
from math import radians
from os import path

import bpy
from bpy.types import Operator, Context, NodeTree, Image

from ..bpy_register import bpy_register
from ..utils import NodeBuilder, arrange_nodes, get_hdri_video_path
from ..properties import OWRecorderReferencePropertis


@bpy_register
class OW_RECORDER_OT_generate_world_nodes(Operator):
    """Generates world nodes"""

    bl_idname = "ow_recorder.generate_world_nodes"
    bl_label = "Generate world shader nodes"

    def execute(self, context: Context):
        scene = context.scene
        reference_props = OWRecorderReferencePropertis.from_context(context)

        hdri_video_path = get_hdri_video_path(context)
        if reference_props.hdri_image is None:
            if not path.isfile(hdri_video_path):
                self.report({"ERROR"}, "rendered HDRI footage not found")
                return {"CANCELLED"}
        else:
            bpy.data.images.remove(reference_props.hdri_image, do_unlink=True)

        hdri_image: Image = bpy.data.images.load(hdri_video_path)
        hdri_image.name = f"Outer Wilds {scene.name} HDRI"
        reference_props.hdri_image = hdri_image

        hdri_node_tree_name = f"Outer Wilds {scene.name} HDRI"
        hdri_node_tree: NodeTree = bpy.data.node_groups.new(
            name=hdri_node_tree_name,
            type=bpy.types.ShaderNodeTree.__name__,
        )

        hdri_node_tree.nodes.clear()
        hdri_node_tree.inputs.clear()
        hdri_node_tree.outputs.clear()

        strength_input = hdri_node_tree.inputs.new(bpy.types.NodeSocketFloat.__name__, "Strength")

        hdri_node_tree.outputs.new(bpy.types.NodeSocketShader.__name__, "Background")

        default_strength = 3
        strength_input.default_value = default_strength
        strength_input.min_value = 0

        def init_environment_node(node: bpy.types.ShaderNodeTexEnvironment):
            node.image = hdri_image
            image_user = node.image_user

            image_user.frame_duration = 1
            image_user.use_auto_refresh = True

            frame_driver = image_user.driver_add("frame_offset").driver

            frame_start_variable = frame_driver.variables.new()
            frame_start_variable.name = "frame_start"
            frame_start_variable.type = "SINGLE_PROP"
            frame_start_variable.targets[0].id_type = "SCENE"
            frame_start_variable.targets[0].id = scene
            frame_start_variable.targets[0].data_path = "frame_start"

            frame_driver.expression = "frame - frame_start"

        with NodeBuilder(hdri_node_tree, bpy.types.NodeGroupOutput) as output_node:
            with output_node.build_input(0, bpy.types.ShaderNodeBackground) as background_node:
                with background_node.build_input("Color", bpy.types.ShaderNodeTexEnvironment) as environment_node:
                    environment_node.defer_init(init_environment_node)

                    with environment_node.build_input("Vector", bpy.types.ShaderNodeMapping) as mapping_node:
                        mapping_node.set_input_value("Rotation", Euler((radians(90), 0, radians(-90))))

                        with mapping_node.build_input("Vector", bpy.types.ShaderNodeTexCoord) as texture_coord_node:
                            texture_coord_node.set_main_output("Generated")

                with background_node.build_input("Strength", bpy.types.NodeGroupInput) as input_node:
                    input_node.set_main_output("Strength")

        arrange_nodes(hdri_node_tree)

        warning_label_node = hdri_node_tree.nodes.new(bpy.types.NodeReroute.__name__)
        warning_label_node.label = "This node tree is auto-generated!"
        warning_label_node.location = (75, 35)

        old_hdri_node_tree: NodeTree = reference_props.hdri_node_tree
        if old_hdri_node_tree is not None:
            old_hdri_node_tree.user_remap(hdri_node_tree)
            bpy.data.node_groups.remove(old_hdri_node_tree, do_unlink=True)
        reference_props.hdri_node_tree = hdri_node_tree

        hdri_node_tree.name = hdri_node_tree_name

        if (
            (scene_world := scene.world) is None
            or (not scene_world.use_nodes)
            or self._is_default_shader(scene_world.node_tree)
        ):
            scene_world = scene.world = scene_world or bpy.data.worlds.new(f"{scene.name} World")
            scene_world.use_nodes = True
            world_node_tree = scene_world.node_tree
            world_node_tree.nodes.clear()

            with NodeBuilder(world_node_tree, bpy.types.ShaderNodeOutputWorld) as output_node:
                with output_node.build_input("Surface", bpy.types.ShaderNodeGroup) as addon_node_group:
                    addon_node_group.set_main_output("Background")
                    addon_node_group.set_attr("node_tree", hdri_node_tree)
                    addon_node_group.set_input_value("Strength", default_strength)

            arrange_nodes(world_node_tree)
        else:
            world_node_tree = scene_world.node_tree
            if not any(
                node.node_tree == hdri_node_tree
                for node in world_node_tree.nodes
                if isinstance(node, bpy.types.ShaderNodeGroup)
            ):
                self.report(
                    {"WARNING"},
                    f"Scene '{scene.name}' has world shader nodes. Add '{hdri_node_tree.name}' group yourself",
                )

        return {"FINISHED"}

    def _is_default_shader(self, node_tree: NodeTree):
        return set(type(node) for node in node_tree.nodes) == {
            bpy.types.ShaderNodeBackground,
            bpy.types.ShaderNodeOutputWorld,
        }
