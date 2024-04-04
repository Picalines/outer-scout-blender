import bpy
from bpy.types import ID, Operator

from ..bpy_register import bpy_register
from ..properties import SceneProperties
from ..utils import NodeBuilder, PostfixNodeBuilder, arrange_nodes, operator_do


@bpy_register
class GenerateCompositorNodesOperator(Operator):
    """Generates compositor nodes"""

    bl_idname = "ow_recorder.generate_compositor_nodes"
    bl_label = "Generate compositor nodes"

    @classmethod
    def poll(cls, context) -> bool:
        return SceneProperties.from_context(context).is_scene_created

    @operator_do
    def execute(self, context):
        scene = context.scene
        scene_props = SceneProperties.from_context(context)

        if scene_props.compositor_node_group:
            comp_node_group = scene_props.compositor_node_group
        else:
            comp_node_group = bpy.data.node_groups.new(
                name=f"Compositing.{scene.name}", type=bpy.types.CompositorNodeTree.__name__
            )
            scene_props.compositor_node_group = comp_node_group

        comp_node_group.nodes.clear()

        IMAGE_IN = "Image Pass"
        DEPTH_IN = "Depth Pass"
        BLUR_IN = "Blur Edges"
        IMAGE_OUT = "Image"

        if set(comp_node_group.interface.items_tree.keys()) != {
            IMAGE_IN,
            DEPTH_IN,
            BLUR_IN,
            IMAGE_OUT,
        }:
            comp_node_group.interface.clear()

            comp_node_group.interface.new_socket(IMAGE_IN, socket_type="NodeSocketColor", in_out="INPUT")
            comp_node_group.interface.new_socket(DEPTH_IN, socket_type="NodeSocketFloat", in_out="INPUT")
            blur_input = comp_node_group.interface.new_socket(BLUR_IN, socket_type="NodeSocketFloat", in_out="INPUT")
            comp_node_group.interface.new_socket(IMAGE_OUT, socket_type="NodeSocketColor", in_out="OUTPUT")

            blur_input.default_value = 0.3
            blur_input.min_value = 0
            blur_input.max_value = 1

        def init_driver_property(expression: str, *variables: tuple[str, str, ID, str]):
            def init(node: bpy.types.CompositorNodeValue):
                value_driver = node.outputs[0].driver_add("default_value").driver

                for name, id_type, id, data_path in variables:
                    variable = value_driver.variables.new()
                    variable.name = name
                    variable.type = "SINGLE_PROP"
                    variable_target = variable.targets[0]

                    variable_target.id_type = id_type
                    variable_target.id = id
                    variable_target.data_path = data_path

                value_driver.expression = expression

            return init

        with NodeBuilder(comp_node_group, bpy.types.NodeGroupOutput) as output_node:
            # TODO
            if recorder_props.record_depth:
                with output_node.build_input(0, bpy.types.CompositorNodeZcombine) as z_combine_node:
                    z_combine_node.set_attr("use_alpha", True)

                    with z_combine_node.build_input(0, bpy.types.NodeGroupInput) as group_input_node:
                        group_input_node.set_main_output(IMAGE_IN)

                    z_combine_node.defer_connect(1, group_input_node, DEPTH_IN)

                    with z_combine_node.build_input(2, bpy.types.CompositorNodeMovieClip) as color_movie_node:
                        color_movie_node.set_main_output("Image")
                        color_movie_node.set_attr("clip", reference_props.main_color_movie_clip)

                    with PostfixNodeBuilder(
                        comp_node_group, "far far near / 1 - raw_depth * 1 + /".split()
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
                                init_driver_property("clip_end", ("clip_end", "SCENE", scene, "camera.data.clip_end"))
                            )

                        depth_expr_node.map_connect("far", far_value_node)

                        with output_node.sibling_builder(bpy.types.CompositorNodeValue) as near_value_node:
                            near_value_node.set_attr("label", "camera_near")
                            near_value_node.set_output_value("Value", camera.clip_start)
                            near_value_node.defer_init(
                                init_driver_property(
                                    "clip_start", ("clip_start", "SCENE", scene, "camera.data.clip_start")
                                )
                            )

                        depth_expr_node.map_connect("near", near_value_node)

                        with output_node.sibling_builder(bpy.types.CompositorNodeSepRGBA) as raw_depth_node:
                            raw_depth_node.set_main_output("R")

                            with raw_depth_node.build_input("Image", bpy.types.CompositorNodeBlur) as blur_node:
                                blur_node.set_attr("size_x", 10)
                                blur_node.set_attr("size_y", 10)

                                with blur_node.build_input("Size", bpy.types.NodeGroupInput) as group_input_node:
                                    group_input_node.set_main_output(BLUR_IN)

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
                    group_input_node.set_main_output(IMAGE_IN)

        arrange_nodes(comp_node_group)

        warning_label_node = comp_node_group.nodes.new(bpy.types.NodeReroute.__name__)
        warning_label_node.label = "This node tree is auto-generated!"
        warning_label_node.location = (75, 35)

        context.view_layer.use_pass_z = True

        self.report({"INFO"}, f"node group '{comp_node_group.name}' generated successfully")
