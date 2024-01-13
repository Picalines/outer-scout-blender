from os import path

import bpy
from bpy.types import ID, Camera, Context, MovieClip, NodeTree, Operator

from ..bpy_register import bpy_register
from ..properties import OWRecorderProperties, OWRecorderReferenceProperties
from ..utils import NodeBuilder, PostfixNodeBuilder, arrange_nodes, get_camera_depth_footage_path, get_id_type


@bpy_register
class OW_RECORDER_OT_generate_compositor_nodes(Operator):
    """Generates compositor nodes"""

    bl_idname = "ow_recorder.generate_compositor_nodes"
    bl_label = "Generate compositor nodes"

    def execute(self, context: Context):
        scene = context.scene
        camera: Camera = scene.camera.data

        reference_props = OWRecorderReferenceProperties.from_context(context)
        recorder_props = OWRecorderProperties.from_context(context)

        if reference_props.main_color_movie_clip is None:
            bpy.ops.ow_recorder.load_camera_background()

        if recorder_props.record_depth:
            depth_video_path = get_camera_depth_footage_path(context, 0)
            if reference_props.main_depth_movie_clip is None:
                if not path.isfile(depth_video_path):
                    self.report({"ERROR"}, "recorded depth footage not found")
                    return {"CANCELLED"}
            else:
                bpy.data.movieclips.remove(reference_props.main_depth_movie_clip, do_unlink=True)

            depth_movie_clip: MovieClip = bpy.data.movieclips.load(depth_video_path)
            depth_movie_clip.name = f"Outer Wilds {scene.name} depth"
            depth_movie_clip.frame_start = scene.frame_start
            reference_props.main_depth_movie_clip = depth_movie_clip

        ow_compositor_node_tree_name = f"Outer Wilds {scene.name} Compositor"
        ow_compositor_node_tree: NodeTree = bpy.data.node_groups.new(
            name=ow_compositor_node_tree_name,
            type=bpy.types.CompositorNodeTree.__name__,
        )

        ow_compositor_node_tree.nodes.clear()
        ow_compositor_node_tree.interface.clear()

        image_pass_input = ow_compositor_node_tree.interface.new_socket(
            "Image Pass", socket_type=bpy.types.NodeSocketColor.__name__, in_out="INPUT"
        )
        depth_pass_input = ow_compositor_node_tree.interface.new_socket(
            "Depth Pass", socket_type=bpy.types.NodeSocketFloat.__name__, in_out="INPUT"
        )

        blur_input = ow_compositor_node_tree.interface.new_socket(
            "Blur Edges", socket_type=bpy.types.NodeSocketFloat.__name__, in_out="INPUT"
        )
        blur_input.default_value = 0.3
        blur_input.min_value = 0
        blur_input.max_value = 1

        ow_compositor_node_tree.interface.new_socket(
            "Image", socket_type=bpy.types.NodeSocketColor.__name__, in_out="OUTPUT"
        )

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

        with NodeBuilder(ow_compositor_node_tree, bpy.types.NodeGroupOutput) as output_node:
            if recorder_props.record_depth:
                with output_node.build_input(0, bpy.types.CompositorNodeZcombine) as z_combine_node:
                    z_combine_node.set_attr("use_alpha", True)

                    with z_combine_node.build_input(0, bpy.types.NodeGroupInput) as group_input_node:
                        group_input_node.set_main_output(image_pass_input.name)

                    z_combine_node.defer_connect(1, group_input_node, depth_pass_input.name)

                    with z_combine_node.build_input(2, bpy.types.CompositorNodeMovieClip) as color_movie_node:
                        color_movie_node.set_main_output("Image")
                        color_movie_node.set_attr("clip", reference_props.main_color_movie_clip)

                    with PostfixNodeBuilder(
                        ow_compositor_node_tree, "far far near / 1 - raw_depth * 1 + /".split()
                    ) as depth_expr_node:
                        math_node_type = bpy.types.CompositorNodeMath
                        depth_expr_node.map_new("+", math_node_type, connect=[1, 0], attrs={"operation": "ADD"})
                        depth_expr_node.map_new("-", math_node_type, connect=[1, 0], attrs={"operation": "SUBTRACT"})
                        depth_expr_node.map_new("*", math_node_type, connect=[1, 0], attrs={"operation": "MULTIPLY"})
                        depth_expr_node.map_new("/", math_node_type, connect=[1, 0], attrs={"operation": "DIVIDE"})

                        depth_expr_node.map_new("1", bpy.types.CompositorNodeValue, outputs={"Value": 1})

                        with output_node.sibling_builder(bpy.types.CompositorNodeValue) as far_value_node:
                            far_value_node.set_attr("label", "camera_far")
                            far_value_node.set_output_value("Value", camera.clip_end)
                            far_value_node.defer_init(
                                init_driver_property(
                                    "clip_end",
                                    ("clip_end", scene, "camera.data.clip_end"),
                                )
                            )

                        depth_expr_node.map_connect("far", far_value_node)

                        with output_node.sibling_builder(bpy.types.CompositorNodeValue) as near_value_node:
                            near_value_node.set_attr("label", "camera_near")
                            near_value_node.set_output_value("Value", camera.clip_start)
                            near_value_node.defer_init(
                                init_driver_property(
                                    "clip_start",
                                    (
                                        "clip_start",
                                        scene,
                                        "camera.data.clip_start",
                                    ),
                                )
                            )

                        depth_expr_node.map_connect("near", near_value_node)

                        with output_node.sibling_builder(bpy.types.CompositorNodeSepRGBA) as raw_depth_node:
                            raw_depth_node.set_main_output("R")

                            with raw_depth_node.build_input("Image", bpy.types.CompositorNodeBlur) as blur_node:
                                blur_node.set_attr("size_x", 10)
                                blur_node.set_attr("size_y", 10)

                                with blur_node.build_input("Size", bpy.types.NodeGroupInput) as group_input_node:
                                    group_input_node.set_main_output(blur_input.name)

                                with blur_node.build_input("Image", bpy.types.CompositorNodeScale) as scale_node:
                                    scale_node.set_attr("space", "RENDER_SIZE")

                                    with scale_node.build_input(
                                        "Image", bpy.types.CompositorNodeMovieClip
                                    ) as depth_movie_node:
                                        depth_movie_node.set_main_output("Image")
                                        depth_movie_node.set_attr("clip", depth_movie_clip)

                        depth_expr_node.map_connect("raw_depth", raw_depth_node)

                    z_combine_node.defer_connect(3, depth_expr_node, 0)
            else:
                with output_node.build_input(0, bpy.types.NodeGroupInput) as group_input_node:
                    group_input_node.set_main_output(image_pass_input.name)

        arrange_nodes(ow_compositor_node_tree)

        warning_label_node = ow_compositor_node_tree.nodes.new(bpy.types.NodeReroute.__name__)
        warning_label_node.label = "This node tree is auto-generated!"
        warning_label_node.location = (75, 35)

        old_ow_compositor_group: NodeTree = reference_props.compositor_node_tree
        if old_ow_compositor_group is not None:
            old_ow_compositor_group.user_remap(ow_compositor_node_tree)
            bpy.data.node_groups.remove(old_ow_compositor_group, do_unlink=True)
        reference_props.compositor_node_tree = ow_compositor_node_tree

        ow_compositor_node_tree.name = ow_compositor_node_tree_name  # prevent auto .001 postfix

        context.view_layer.use_pass_z = True

        if not scene.use_nodes or self._is_default_compositor(scene.node_tree):
            scene.use_nodes = True
            compositor_node_tree = scene.node_tree
            compositor_node_tree.nodes.clear()
            compositor_node_tree.interface.clear()

            with NodeBuilder(compositor_node_tree, bpy.types.CompositorNodeComposite) as composite_node:
                with composite_node.build_input("Image", bpy.types.CompositorNodeGroup) as addon_group_node:
                    addon_group_node.set_main_output(0)
                    addon_group_node.set_attr("node_tree", ow_compositor_node_tree)

                    with addon_group_node.build_input(
                        image_pass_input.name, bpy.types.CompositorNodeRLayers
                    ) as render_node:
                        render_node.set_main_output("Image")
                        render_node.set_attr("scene", scene)

                    addon_group_node.defer_connect(depth_pass_input.name, render_node, "Depth")

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
        return len(node_tree.nodes) == 2 and set(type(node) for node in node_tree.nodes) == {
            bpy.types.CompositorNodeRLayers,
            bpy.types.CompositorNodeComposite,
        }

