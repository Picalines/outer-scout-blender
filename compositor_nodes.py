from pathlib import Path

import bpy
from bpy.types import Scene

from .ow_scene_data import OWSceneData
from .node_utils import NodeBuilder, create_node, arrange_nodes


def set_compositor_nodes(owscene_filepath: str, scene: Scene, ow_data: OWSceneData):
    scene.use_nodes = True
    compositor_tree = scene.node_tree

    compositor_tree.nodes.clear()

    def init_z_combine_node(node: bpy.types.CompositorNodeZcombine):
        node.use_alpha = True

    def init_render_layer_node(node: bpy.types.CompositorNodeRLayers):
        node.scene = scene

    def init_background_clip_node(node: bpy.types.CompositorNodeMovieClip):
        node.clip = bpy.data.movieclips['OW_mainCamera']

    def init_depth_clip_node(node: bpy.types.CompositorNodeMovieClip):
        depth_video_path = str(Path(owscene_filepath).parent.joinpath('depth.mp4'))
        node.clip = bpy.data.movieclips.load(depth_video_path)
        node.clip.name = 'OW_depth'

    def init_scale_node(node: bpy.types.CompositorNodeScale):
        node.space = 'RENDER_SIZE'

    def init_erode_node(node: bpy.types.CompositorNodeDilateErode):
        node.distance = -1

    def init_blur_node(node: bpy.types.CompositorNodeBlur):
        node.size_x = node.size_y = 2

    def init_math_node(operation: str):
        def init(node: bpy.types.CompositorNodeMath):
            node.operation = operation

        return init

    def build_math_node(operation: str, *, left: NodeBuilder, right: NodeBuilder):
        return NodeBuilder(bpy.types.CompositorNodeMath,
            init=init_math_node(operation),
            _0=left,
            _1=right)

    def build_value_node(value: float, label = 'Value'):
        def init(node: bpy.types.CompositorNodeValue):
            node.label = label
            node.outputs['Value'].default_value = value

        return NodeBuilder(bpy.types.CompositorNodeValue, init=init)

    z_combine_node = NodeBuilder(bpy.types.CompositorNodeZcombine,
        init=init_z_combine_node,
        _0=NodeBuilder(bpy.types.CompositorNodeExposure,
            Exposure=3,
            Image=(render_layers_node:=NodeBuilder(bpy.types.CompositorNodeRLayers,
                init=init_render_layer_node,
                output='Image',
            )),
        ),
        _1=render_layers_node.connect_output('Depth'),
        _2=NodeBuilder(bpy.types.CompositorNodeMovieClip,
            init=init_background_clip_node,
            output='Image',
        ),
        _3=build_math_node('DIVIDE',
            left=(
                far_value_node:=build_value_node(ow_data['depth_camera']['far_clip_plane'], label='far')
            ),
            right=build_math_node('ADD',
                left=build_math_node('MULTIPLY',
                    left=build_math_node('SUBTRACT',
                        left=build_math_node('DIVIDE',
                            left=far_value_node,
                            right=build_value_node(ow_data['depth_camera']['near_clip_plane'], label='near'),
                        ),
                        right=1,
                    ),
                    right=NodeBuilder(bpy.types.CompositorNodeDilateErode,
                        init=init_erode_node,
                        Mask=NodeBuilder(bpy.types.CompositorNodeSepRGBA,
                            output='R',
                            Image=NodeBuilder(bpy.types.CompositorNodeBlur,
                                init=init_blur_node,
                                Image=NodeBuilder(bpy.types.CompositorNodeScale,
                                    init=init_scale_node,
                                    Image=NodeBuilder(bpy.types.CompositorNodeMovieClip,
                                        init=init_depth_clip_node,
                                        output='Image',
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
                right=1,
            )
        )
    ).build(compositor_tree)

    composite_node = create_node(compositor_tree, bpy.types.CompositorNodeComposite)
    viewer_node = create_node(compositor_tree, bpy.types.CompositorNodeViewer)

    compositor_tree.links.new(z_combine_node.outputs['Image'], composite_node.inputs['Image'])
    compositor_tree.links.new(z_combine_node.outputs['Image'], viewer_node.inputs['Image'])

    arrange_nodes(compositor_tree)
