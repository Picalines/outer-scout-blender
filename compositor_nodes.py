from pathlib import Path

import bpy
from bpy.types import Scene

from .ow_json_data import OWSceneData
from .utils import NodeBuilder, create_node, arrange_nodes


def set_compositor_nodes(owscene_filepath: str, scene: Scene, ow_data: OWSceneData):
    scene.use_nodes = True
    compositor_tree = scene.node_tree

    compositor_tree.nodes.clear()

    def init_depth_clip_node(node: bpy.types.CompositorNodeMovieClip):
        depth_video_path = str(Path(owscene_filepath).parent.joinpath("depth.mp4"))
        node.clip = bpy.data.movieclips.load(depth_video_path)
        node.clip.name = "OW_depth"

    def build_math_node(operation: str, *, left: NodeBuilder, right: NodeBuilder):
        return NodeBuilder(
            bpy.types.CompositorNodeMath, operation=operation, _0=left, _1=right
        )

    def build_value_node(value: float, label="Value"):
        def init(node: bpy.types.CompositorNodeValue):
            node.label = label
            node.outputs["Value"].default_value = value

        return NodeBuilder(bpy.types.CompositorNodeValue, init=init)

    z_combine_node = NodeBuilder(
        bpy.types.CompositorNodeZcombine,
        use_alpha=True,
        _0=NodeBuilder(
            bpy.types.CompositorNodeExposure,
            Exposure=3,
            Image=(
                render_layers_node := NodeBuilder(
                    bpy.types.CompositorNodeRLayers,
                    scene=scene,
                    output="Image",
                )
            ),
        ),
        _1=render_layers_node.connect_output("Depth"),
        _2=NodeBuilder(
            bpy.types.CompositorNodeMovieClip,
            clip=bpy.data.movieclips["OW_mainCamera"],
            output="Image",
        ),
        _3=build_math_node(
            "DIVIDE",
            left=(
                far_value_node := build_value_node(
                    ow_data["depth_camera"]["far_clip_plane"], label="camera_far"
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
                                ow_data["depth_camera"]["near_clip_plane"],
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
                                        init=init_depth_clip_node,
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
    ).build(compositor_tree)

    composite_node = create_node(compositor_tree, bpy.types.CompositorNodeComposite)
    viewer_node = create_node(compositor_tree, bpy.types.CompositorNodeViewer)

    compositor_tree.links.new(
        z_combine_node.outputs["Image"], composite_node.inputs["Image"]
    )
    compositor_tree.links.new(
        z_combine_node.outputs["Image"], viewer_node.inputs["Image"]
    )

    arrange_nodes(compositor_tree)
