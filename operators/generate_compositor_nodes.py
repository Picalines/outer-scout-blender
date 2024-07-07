from typing import Callable

import bpy
from math import inf
from bpy.types import MovieClip, Object, Operator, Scene

from ..bpy_register import bpy_register
from ..properties import CameraProperties, SceneProperties
from ..utils import NodeBuilder, NodeTreeInterfaceBuilder, PostfixNodeBuilder, add_driver, arrange_nodes, operator_do

CAMERA_ID_CUSTOM_PROP = "outer_scout.camera_id"


@bpy_register
class GenerateCompositorNodesOperator(Operator):
    """Generates compositor nodes"""

    bl_idname = "outer_scout.generate_compositor_nodes"
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

        cameras: list[Object] = [
            camera_object
            for (camera_object, camera_props) in (
                (camera_object, CameraProperties.of_camera(camera_object.data))
                for camera_object in scene.objects
                if camera_object.type == "CAMERA"
            )
            if camera_props.is_active and camera_props.outer_scout_type == "PERSPECTIVE"
        ]

        for i, camera_object in enumerate(cameras):
            camera_object[CAMERA_ID_CUSTOM_PROP] = i

        comp_node_group.nodes.clear()

        IMAGE_IN = "Image"
        DEPTH_IN = "Z"
        BLUR_IN = "Blur Edges"
        IMAGE_OUT = "Image"
        BACKGROUND_OUT = "Background"
        DEPTH_OUT = "Z"

        with NodeTreeInterfaceBuilder(comp_node_group.interface) as interface_builder:
            interface_builder.add_input(IMAGE_IN, bpy.types.NodeSocketColor, default_value=(0, 0, 0, 0))
            interface_builder.add_input(DEPTH_IN, bpy.types.NodeSocketFloat, default_value=inf, hide_value=True)
            interface_builder.add_input(BLUR_IN, bpy.types.NodeSocketFloat, default_value=0.3, min_value=0, max_value=1)
            interface_builder.add_output(IMAGE_OUT, bpy.types.NodeSocketColor, default_value=(0, 0, 0, 0))
            interface_builder.add_output(BACKGROUND_OUT, bpy.types.NodeSocketColor)
            interface_builder.add_output(DEPTH_OUT, bpy.types.NodeSocketFloat)

        with NodeBuilder(comp_node_group, bpy.types.NodeGroupOutput) as output_node:
            with output_node.build_input(IMAGE_OUT, bpy.types.CompositorNodeZcombine) as z_combine_node:
                output_node.defer_connect(DEPTH_OUT, z_combine_node, 1)

                z_combine_node.set_attr("use_alpha", True)

                with z_combine_node.build_input(0, bpy.types.NodeGroupInput) as group_input_node:
                    group_input_node.set_main_output(IMAGE_IN)

                z_combine_node.defer_connect(1, group_input_node, DEPTH_IN)

                background_node = self._build_camera_clip_switch(
                    z_combine_node,
                    2,
                    scene=scene,
                    cameras=cameras,
                    get_clip=lambda c: CameraProperties.of_camera(c.data).color_texture_props.movie_clip,
                )

                if background_node is not None:
                    output_node.defer_connect(BACKGROUND_OUT, background_node, "Image")

                with PostfixNodeBuilder(
                    comp_node_group, "far far near / 1 - raw_depth * 1 + /".split()
                ) as depth_expr_node:
                    math_node_type = bpy.types.CompositorNodeMath
                    depth_expr_node.map_new("+", math_node_type, connect=[1, 0], attrs={"operation": "ADD"})
                    depth_expr_node.map_new("-", math_node_type, connect=[1, 0], attrs={"operation": "SUBTRACT"})
                    depth_expr_node.map_new("*", math_node_type, connect=[1, 0], attrs={"operation": "MULTIPLY"})
                    depth_expr_node.map_new("/", math_node_type, connect=[1, 0], attrs={"operation": "DIVIDE"})

                    depth_expr_node.map_new("1", bpy.types.CompositorNodeValue, outputs={"Value": 1})

                    with output_node.sibling_builder(bpy.types.CompositorNodeValue) as near_value_node:
                        near_value_node.set_attr("label", "camera_near")
                        near_value_node.defer_init(
                            lambda node: add_driver(
                                node.outputs[0],
                                "default_value",
                                "clip_start",
                                clip_start=(scene, "camera.data.clip_start"),
                            )
                        )

                    with output_node.sibling_builder(bpy.types.CompositorNodeValue) as far_value_node:
                        far_value_node.set_attr("label", "camera_far")
                        far_value_node.defer_init(
                            lambda node: add_driver(
                                node.outputs[0], "default_value", "clip_end", clip_end=(scene, "camera.data.clip_end")
                            )
                        )

                    depth_expr_node.map_connect("near", near_value_node)
                    depth_expr_node.map_connect("far", far_value_node)

                    with output_node.sibling_builder(bpy.types.CompositorNodeSepRGBA) as raw_depth_node:
                        raw_depth_node.set_main_output("R")

                        with raw_depth_node.build_input("Image", bpy.types.CompositorNodeBlur) as blur_node:
                            blur_node.set_attr("size_x", 10)
                            blur_node.set_attr("size_y", 10)

                            with blur_node.build_input("Size", bpy.types.NodeGroupInput) as group_input_node:
                                group_input_node.set_main_output(BLUR_IN)

                            with blur_node.build_input("Image", bpy.types.CompositorNodeScale) as scale_node:
                                scale_node.set_attr("space", "RENDER_SIZE")

                                self._build_camera_clip_switch(
                                    scale_node,
                                    "Image",
                                    scene=scene,
                                    cameras=cameras,
                                    get_clip=lambda c: CameraProperties.of_camera(
                                        c.data
                                    ).depth_texture_props.movie_clip,
                                )

                    depth_expr_node.map_connect("raw_depth", raw_depth_node)

                z_combine_node.defer_connect(3, depth_expr_node, 0)

        arrange_nodes(comp_node_group)

        warning_label_node = comp_node_group.nodes.new(bpy.types.NodeReroute.__name__)
        warning_label_node.label = "This node tree is auto-generated!"
        warning_label_node.location = (75, 35)

        context.view_layer.use_pass_z = True

        self.report({"INFO"}, f"node group '{comp_node_group.name}' generated successfully")

    def _build_camera_clip_switch(
        self,
        dest_builder: NodeBuilder,
        dest_input: int | str,
        *,
        scene: Scene,
        cameras: list[Object],
        get_clip: Callable[[Object], MovieClip | None],
        _camera_index=0,
    ) -> NodeBuilder | None:
        if not len(cameras):
            return None

        with dest_builder.build_input(dest_input, bpy.types.CompositorNodeMixRGB) as mix_node:
            mix_node.set_attr("blend_type", "MIX")

            mix_node.defer_init(
                lambda node: add_driver(
                    node.inputs["Fac"],
                    "default_value",
                    "current_camera == checked_camera",
                    current_camera=(scene, f'camera["{CAMERA_ID_CUSTOM_PROP}"]'),
                    checked_camera=(cameras[_camera_index], f'["{CAMERA_ID_CUSTOM_PROP}"]'),
                )
            )

            movie_clip = get_clip(cameras[_camera_index])
            if movie_clip:
                with mix_node.build_input(2, bpy.types.CompositorNodeMovieClip) as movie_clip_node:
                    movie_clip_node.set_main_output("Image")
                    movie_clip_node.set_attr("clip", movie_clip)
            else:
                mix_node.set_input_value(2, (0, 0, 0, 1))

            if _camera_index + 1 < len(cameras):
                self._build_camera_clip_switch(
                    mix_node, 1, scene=scene, cameras=cameras, get_clip=get_clip, _camera_index=_camera_index + 1
                )
            else:
                mix_node.set_input_value(1, (0, 0, 0, 1))

        return mix_node
