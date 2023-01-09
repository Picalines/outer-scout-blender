from mathutils import Euler
from math import radians
from pathlib import Path

import bpy
from bpy.types import Scene

from .ow_json_data import OWSceneData
from .node_utils import NodeBuilder, arrange_nodes

def set_world_nodes(owscene_filepath: str, scene: Scene, ow_data: OWSceneData):
    node_tree = (scene.world or bpy.data.worlds.new(f'{scene.name}.World')).node_tree
    node_tree.nodes.clear()

    def init_environment_node(node: bpy.types.ShaderNodeTexEnvironment):
        hdri_video_path = str(Path(owscene_filepath).parent.joinpath("hdri.mp4"))

        node.image = bpy.data.images.load(hdri_video_path)
        node.image.name = 'OW_HDRI'
        node.image_user.frame_duration = ow_data["recorded_frames"]
        node.image_user.use_auto_refresh = True
        node.image_user.driver_add("frame_offset").driver.expression = "frame"

    NodeBuilder(bpy.types.ShaderNodeOutputWorld,
        Surface=NodeBuilder(bpy.types.ShaderNodeBackground,
            Color=NodeBuilder(bpy.types.ShaderNodeTexEnvironment,
                init=init_environment_node,
                Vector=NodeBuilder(bpy.types.ShaderNodeMapping,
                    Rotation=Euler((0, 0, radians(-90))),
                    Vector=NodeBuilder(bpy.types.ShaderNodeTexCoord, output="Generated")
                )
            )
        )
    ).build(node_tree)

    arrange_nodes(node_tree)
