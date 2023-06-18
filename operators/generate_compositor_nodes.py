from os import path

import bpy
from bpy.types import Operator, Context, NodeTree, MovieClip, Camera

from ..bpy_register import bpy_register
from ..utils import NodeBuilder, arrange_nodes, get_depth_video_path
from ..properties import OWRecorderReferencePropertis


@bpy_register
class OW_RECORDER_OT_generate_compositor_nodes(Operator):
    """Generates compositor nodes"""

    bl_idname = "ow_recorder.generate_compositor_nodes"
    bl_label = "Generate compositor nodes"

    def execute(self, context: Context):
        scene = context.scene
        camera: Camera = scene.camera.data

        reference_props = OWRecorderReferencePropertis.from_context(context)

        if reference_props.background_movie_clip is None:
            bpy.ops.ow_recorder.load_camera_background()

        depth_video_path = get_depth_video_path(context)
        if reference_props.depth_movie_clip is None:
            if not path.isfile(depth_video_path):
                self.report({"ERROR"}, "rendered depth footage not found")
                return {"CANCELLED"}
        else:
            bpy.data.movieclips.remove(reference_props.depth_movie_clip, do_unlink=True)

        depth_movie_clip: MovieClip = bpy.data.movieclips.load(depth_video_path)
        depth_movie_clip.name = f"Outer Wilds {scene.name} depth"
        depth_movie_clip.frame_start = scene.frame_start
        reference_props.depth_movie_clip = depth_movie_clip

        ow_compositor_node_tree: NodeTree = bpy.data.node_groups.new(
            name=f"Outer Wilds {scene.name} Compositor",
            type=bpy.types.CompositorNodeTree.__name__,
        )

        ow_compositor_node_tree.nodes.clear()
        ow_compositor_node_tree.inputs.clear()
        ow_compositor_node_tree.outputs.clear()

        ow_compositor_node_tree.inputs.new(bpy.types.NodeSocketColor.__name__, "Image")
        ow_compositor_node_tree.inputs.new(bpy.types.NodeSocketFloat.__name__, "Depth")
        ow_compositor_node_tree.outputs.new(bpy.types.NodeSocketColor.__name__, "Image")

        def build_math_node(operation: str, *, left: NodeBuilder, right: NodeBuilder):
            return NodeBuilder(
                bpy.types.CompositorNodeMath, operation=operation, _0=left, _1=right
            )

        def build_value_node(value: float, label="Value"):
            def init(node: bpy.types.CompositorNodeValue):
                node.label = label
                node.outputs["Value"].default_value = value

            return NodeBuilder(bpy.types.CompositorNodeValue, init=init)

        NodeBuilder(
            bpy.types.NodeGroupOutput,
            _0=NodeBuilder(
                bpy.types.CompositorNodeZcombine,
                use_alpha=True,
                _0=(
                    group_input_node := NodeBuilder(
                        bpy.types.NodeGroupInput, output="Image"
                    )
                ),
                _1=group_input_node.connect_output("Depth"),
                _2=NodeBuilder(
                    bpy.types.CompositorNodeMovieClip,
                    clip=reference_props.background_movie_clip,
                    output="Image",
                ),
                _3=build_math_node(
                    "DIVIDE",
                    left=(
                        far_value_node := build_value_node(
                            camera.clip_end, label="camera_far"  # TODO: driver
                        )
                    ),
                    right=build_math_node(
                        "ADD",
                        left=build_math_node(
                            "MULTIPLY",
                            left=build_math_node(
                                "SUBTRACT",
                                left=build_math_node(
                                    "DIVIDE",
                                    left=far_value_node,
                                    right=build_value_node(
                                        camera.clip_start,  # TODO: driver
                                        label="camera_near",
                                    ),
                                ),
                                right=1,
                            ),
                            right=NodeBuilder(
                                bpy.types.CompositorNodeDilateErode,
                                distance=-1,
                                Mask=NodeBuilder(
                                    bpy.types.CompositorNodeSepRGBA,
                                    output="R",
                                    Image=NodeBuilder(
                                        bpy.types.CompositorNodeBlur,
                                        size_x=2,
                                        size_y=2,
                                        Image=NodeBuilder(
                                            bpy.types.CompositorNodeScale,
                                            space="RENDER_SIZE",
                                            Image=NodeBuilder(
                                                bpy.types.CompositorNodeMovieClip,
                                                clip=depth_movie_clip,
                                                output="Image",
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        right=1,
                    ),
                ),
            ),
        ).build(ow_compositor_node_tree)

        arrange_nodes(ow_compositor_node_tree)

        old_ow_compositor_group: NodeTree = reference_props.compositor_node_tree
        if old_ow_compositor_group is not None:
            old_ow_compositor_group.user_remap(ow_compositor_node_tree)
            bpy.data.node_groups.remove(old_ow_compositor_group, do_unlink=True)
        reference_props.compositor_node_tree = ow_compositor_node_tree

        context.view_layer.use_pass_z = True

        if not scene.use_nodes or self._is_default_compositor(scene.node_tree):
            scene.use_nodes = True
            compositor_node_tree = scene.node_tree
            compositor_node_tree.nodes.clear()

            NodeBuilder(
                bpy.types.CompositorNodeComposite,
                Image=NodeBuilder(
                    bpy.types.CompositorNodeGroup,
                    node_tree=ow_compositor_node_tree,
                    output="Image",
                    Image=(
                        render_layers_node := NodeBuilder(
                            bpy.types.CompositorNodeRLayers, scene=scene, output="Image"
                        )
                    ),
                    Depth=render_layers_node.connect_output("Depth"),
                ),
            ).build(compositor_node_tree)

            arrange_nodes(compositor_node_tree)
        else:
            compositor_node_tree = scene.node_tree
            if not any(
                node.node_tree == ow_compositor_node_tree
                for node in compositor_node_tree.nodes
                if isinstance(node, bpy.types.CompositorNodeGroup)
            ):
                self.report(
                    {"WARNING"},
                    f"Scene '{scene.name}' has compositor nodes. Add '{ow_compositor_node_tree.name}' group yourself",
                )

        return {"FINISHED"}

    def _is_default_compositor(self, node_tree: NodeTree):
        return set(
            type(node)
            for node in node_tree.nodes
            if type(node) != bpy.types.CompositorNodeViewer
        ) == {bpy.types.CompositorNodeRLayers, bpy.types.CompositorNodeComposite}
