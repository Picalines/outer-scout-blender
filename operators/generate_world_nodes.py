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

        hdri_frame_duration = scene.frame_end - scene.frame_start + 1

        hdri_image: Image = bpy.data.images.load(hdri_video_path)
        # TODO: frame_start???
        reference_props.hdri_image = hdri_image

        def init_environment_node(node: bpy.types.ShaderNodeTexEnvironment):
            node.image = hdri_image
            image_user = node.image_user

            image_user.frame_duration = hdri_frame_duration
            image_user.use_auto_refresh = True
            image_user.driver_add("frame_offset").driver.expression = "frame"

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
            ),
        ).build(hdri_node_tree)
        arrange_nodes(hdri_node_tree)

        scene_world = scene.world
        if scene_world is None or not scene_world.use_nodes:
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
