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

        hdri_node_tree: NodeTree = (
            reference_props.hdri_node_tree
            or bpy.data.node_groups.new(
                name=f"Outer Wilds {scene.name} HDRI",
                type=bpy.types.ShaderNodeTree.__name__,
            )
        )

        reference_props.hdri_node_tree = hdri_node_tree
        hdri_node_tree.nodes.clear()

        hdri_video_path = get_hdri_video_path(context)
        if reference_props.hdri_image is None:
            if not path.isfile(hdri_video_path):
                self.report({"ERROR"}, "rendered HDRI footage not found")
                return {"CANCELLED"}
        else:
            bpy.data.images.remove(reference_props.hdri_image, do_unlink=True)

        hdri_image: Image = bpy.data.images.load(hdri_video_path)
        reference_props.hdri_image = hdri_image

        strength_input: bpy.types.NodeSocketInterfaceFloat = next(
            (
                input
                for input in hdri_node_tree.inputs
                if input.name == "Strength"
                and isinstance(input, bpy.types.NodeSocketInterfaceFloat)
            ),
            None,
        )

        strength_input = strength_input or hdri_node_tree.inputs.new(
            bpy.types.NodeSocketFloat.__name__, "Strength"
        )

        for input in hdri_node_tree.inputs:
            if input != strength_input:
                hdri_node_tree.inputs.remove(input)

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

        NodeBuilder(
            bpy.types.NodeGroupOutput,
            _0=NodeBuilder(
                bpy.types.ShaderNodeBackground,
                Color=NodeBuilder(
                    bpy.types.ShaderNodeTexEnvironment,
                    init=init_environment_node,
                    Vector=NodeBuilder(
                        bpy.types.ShaderNodeMapping,
                        Rotation=Euler((0, radians(-90), 0)),
                        Vector=NodeBuilder(
                            bpy.types.ShaderNodeTexCoord,
                            output="Generated",
                        ),
                    ),
                ),
                Strength=NodeBuilder(
                    bpy.types.NodeGroupInput,
                    output="Strength",
                ),
            ),
        ).build(hdri_node_tree)
        arrange_nodes(hdri_node_tree)

        if (
            (scene_world := scene.world) is None
            or (not scene_world.use_nodes)
            or self._is_default_shader(scene_world.node_tree)
        ):
            scene_world = scene.world = scene_world or bpy.data.worlds.new(
                f"{scene.name} World"
            )
            scene_world.use_nodes = True
            world_node_tree = scene_world.node_tree
            world_node_tree.nodes.clear()

            NodeBuilder(
                bpy.types.ShaderNodeOutputWorld,
                Surface=NodeBuilder(
                    bpy.types.ShaderNodeGroup,
                    node_tree=hdri_node_tree,
                    Strength=default_strength,
                ),
            ).build(world_node_tree)
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
        return len(node_tree.nodes) == 2 and set(
            type(node) for node in node_tree.nodes
        ) == {bpy.types.ShaderNodeBackground, bpy.types.ShaderNodeOutputWorld}
