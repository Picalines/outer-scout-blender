from os import path

import bpy
from bpy.types import ID, Operator, Context, NodeTree, MovieClip, Camera

from ..bpy_register import bpy_register
from ..utils import NodeBuilder, get_id_type, arrange_nodes, get_depth_video_path
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

        ow_compositor_node_tree_name = f"Outer Wilds {scene.name} Compositor"
        ow_compositor_node_tree: NodeTree = bpy.data.node_groups.new(
            name=ow_compositor_node_tree_name,
            type=bpy.types.CompositorNodeTree.__name__,
        )

        ow_compositor_node_tree.nodes.clear()
        ow_compositor_node_tree.inputs.clear()
        ow_compositor_node_tree.outputs.clear()

        image_pass_input = ow_compositor_node_tree.inputs.new(
            bpy.types.NodeSocketColor.__name__, "Image Pass"
        )
        depth_pass_input = ow_compositor_node_tree.inputs.new(
            bpy.types.NodeSocketFloat.__name__, "Depth Pass"
        )

        blur_input = ow_compositor_node_tree.inputs.new(
            bpy.types.NodeSocketFloat.__name__, "Blur Edges"
        )
        blur_input.default_value = 0.3
        blur_input.min_value = 0
        blur_input.max_value = 1

        ow_compositor_node_tree.outputs.new(bpy.types.NodeSocketColor.__name__, "Image")

        def build_math_node(operation: str, *, left: NodeBuilder, right: NodeBuilder):
            return NodeBuilder(
                bpy.types.CompositorNodeMath, operation=operation, _0=left, _1=right
            )

        def build_value_node(value: float, *, label="Value", inits=None):
            inits = [] if inits is None else inits

            def init(node: bpy.types.CompositorNodeValue):
                node.label = label
                node.outputs["Value"].default_value = value

            return NodeBuilder(bpy.types.CompositorNodeValue, init=[init, *inits])

        def init_driver_property(expression: str, *variables: tuple[str, ID, str]):
            def init(node: bpy.types.CompositorNodeValue):
                value_driver = node.outputs[0].driver_add("default_value").driver

                for name, id, data_path in variables:
                    variable = value_driver.variables.new()
                    variable.name = name
                    variable.type = "SINGLE_PROP"
                    variable_target = variable.targets[0]

                    variable_target.id_type = get_id_type(id)
                    variable_target.id = id
                    variable_target.data_path = data_path

                value_driver.expression = expression

            return init

        NodeBuilder(
            bpy.types.NodeGroupOutput,
            _0=NodeBuilder(
                bpy.types.CompositorNodeZcombine,
                use_alpha=True,
                _0=(
                    group_input_node := NodeBuilder(
                        bpy.types.NodeGroupInput, output=image_pass_input.name
                    )
                ),
                _1=group_input_node.connect_output(depth_pass_input.name),
                _2=NodeBuilder(
                    bpy.types.CompositorNodeMovieClip,
                    clip=reference_props.background_movie_clip,
                    output="Image",
                ),
                _3=build_math_node(
                    "DIVIDE",
                    left=(
                        far_value_node := build_value_node(
                            camera.clip_end,
                            label="camera_far",
                            inits=[
                                init_driver_property(
                                    "clip_end",
                                    ("clip_end", scene, "camera.data.clip_end"),
                                )
                            ],
                        )
                    ),
                    right=build_math_node(
                        "ADD",
                        right=1,
                        left=build_math_node(
                            "MULTIPLY",
                            left=build_math_node(
                                "SUBTRACT",
                                left=build_math_node(
                                    "DIVIDE",
                                    left=far_value_node,
                                    right=build_value_node(
                                        camera.clip_start,
                                        label="camera_near",
                                        inits=[
                                            init_driver_property(
                                                "clip_start",
                                                (
                                                    "clip_start",
                                                    scene,
                                                    "camera.data.clip_start",
                                                ),
                                            )
                                        ],
                                    ),
                                ),
                                right=1,
                            ),
                            right=NodeBuilder(
                                bpy.types.CompositorNodeSepRGBA,
                                output="R",
                                Image=NodeBuilder(
                                    bpy.types.CompositorNodeBlur,
                                    size_x=10,
                                    size_y=10,
                                    Size=NodeBuilder(
                                        bpy.types.NodeGroupInput, output=blur_input.name
                                    ),
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
                ),
            ),
        ).build(ow_compositor_node_tree)
        arrange_nodes(ow_compositor_node_tree)

        warning_label_node = ow_compositor_node_tree.nodes.new(
            bpy.types.NodeReroute.__name__
        )
        warning_label_node.label = "This node tree is auto-generated!"
        warning_label_node.location = (75, 35)

        old_ow_compositor_group: NodeTree = reference_props.compositor_node_tree
        if old_ow_compositor_group is not None:
            old_ow_compositor_group.user_remap(ow_compositor_node_tree)
            bpy.data.node_groups.remove(old_ow_compositor_group, do_unlink=True)
        reference_props.compositor_node_tree = ow_compositor_node_tree

        ow_compositor_node_tree.name = (
            ow_compositor_node_tree_name  # prevent auto .001 postfix
        )

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
                    output=image_pass_input.name,
                    Image=(
                        render_layers_node := NodeBuilder(
                            bpy.types.CompositorNodeRLayers, scene=scene, output="Image"
                        )
                    ),
                    Depth=render_layers_node.connect_output(depth_pass_input.name),
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
        return set(type(node) for node in node_tree.nodes) == {
            bpy.types.CompositorNodeRLayers,
            bpy.types.CompositorNodeComposite,
        }
