from pathlib import Path
from math import radians
from typing import Iterable
import os

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator, Object, Camera, Scene
from mathutils import Vector, Quaternion, Euler

from .preferences import OWSceneImporterPreferences
from .node_utils import arrange_nodes, NodeBuilder, create_node
from .ow_scene_data import OWSceneData, TransformData as OWTransformData, load_ow_scene_data


class OWSceneImporter(Operator, ImportHelper):
    bl_idname = "outer_wilds_recorder.importer"
    bl_label = "Import .owscene"

    filename_ext = ".owscene"

    filter_glob : StringProperty(
        default = "*.owscene",
        options = { 'HIDDEN' },
        maxlen= 255
    )

    def execute(self, _):
        preferences: OWSceneImporterPreferences = bpy.context.preferences.addons[__package__].preferences

        current_scene = bpy.context.scene

        ow_data = load_ow_scene_data(self.filepath)

        # create body pivot
        bpy.ops.object.empty_add()
        ow_player_pivot = bpy.context.active_object
        ow_player_pivot.name = 'OW_PlayerPivot'
        self.apply_transform_data(ow_player_pivot, ow_data["player"]["transform"])

        # create player camera pivot
        bpy.ops.object.empty_add()
        player_camera_pivot = bpy.context.active_object
        player_camera_pivot.name = 'PlayerCamera_Pivot'
        self.apply_transform_data(player_camera_pivot, ow_data["player_camera"]["transform"])

        # create camera
        camera = self.create_camera(current_scene, ow_data)

        # import ground_body
        ow_ground_body = self.load_ground_body(ow_data, preferences)
        if ow_ground_body is None:
            self.report({"ERROR"}, f"couldn't load .blend file of '{ow_data['ground_body']['name']}'")

        # move scene to origin
        self.set_parent([camera, player_camera_pivot, ow_ground_body], ow_player_pivot, keep_transform=True)
        ow_player_pivot.location = (0, 0, 0)

        # make X - right, Y - forward, Z - up
        # (like in new General project)
        ow_player_pivot.rotation_mode = 'XYZ'
        ow_player_pivot.rotation_euler = Euler((radians(90), 0, radians(90)), 'XYZ')

        # scene properties
        current_scene.frame_end = ow_data["recorded_frames"]
        current_scene.render.fps = ow_data["recorder_settings"]["framerate"]
        current_scene.render.resolution_x = ow_data["recorder_settings"]["width"]
        current_scene.render.resolution_y = ow_data["recorder_settings"]["height"]
        current_scene.render.film_transparent = True
        bpy.context.view_layer.use_pass_z = True

        # nodes
        self.set_world_hdri_nodes(current_scene, ow_data)
        self.set_compositor_nodes(current_scene, ow_data)

        return {"FINISHED"}

    def create_camera(self, scene: Scene, ow_data: OWSceneData):
        bpy.ops.object.camera_add()
        camera = scene.camera = bpy.context.active_object

        camera_data: Camera = camera.data
        camera_data.type = 'PERSP'
        camera_data.lens_unit = 'FOV'
        camera_data.sensor_fit = 'VERTICAL'
        camera_data.angle = radians(ow_data["background_camera"]["fov"])

        background_video_path = str(Path(self.filepath).parent.joinpath("background.mp4"))

        camera_data.show_background_images = True
        camera_background = camera_data.background_images.new()
        camera_background.source = 'MOVIE_CLIP'
        camera_background.clip = bpy.data.movieclips.load(background_video_path)
        camera_background.clip.name = "OW_mainCamera"
        camera_background.alpha = 1

        render_settings = bpy.context.scene.render
        render_settings.resolution_x, render_settings.resolution_y = camera_background.clip.size

        camera.name = "OW Camera"
        self.apply_transform_data(camera, ow_data["background_camera"]["transform"])
        camera.rotation_quaternion @= Quaternion((0, 1, 0), -radians(90))

        return camera

    def apply_transform_data(self, object: Object, transform_data: OWTransformData):
        object.location = Vector(transform_data["position"])
        object.scale = Vector(transform_data["scale"])
        object.rotation_mode = 'QUATERNION'
        object.rotation_quaternion = Quaternion(transform_data["rotation"])

    def load_ground_body(self, ow_data: OWSceneData, preferences: OWSceneImporterPreferences) -> Object | None:
        ow_body_name = ow_data["ground_body"]["name"]

        ow_body_project_path = os.path.join(preferences.ow_bodies_folder, ow_body_name + ".blend")
        ow_body_project_import_status = bpy.ops.wm.link(
            filepath=os.path.join(ow_body_project_path, "Collection", "Collection"),
            filename="Collection",
            directory=os.path.join(ow_body_project_path, "Collection"))

        if ow_body_project_import_status != {"FINISHED"}:
            return None

        ow_body_link = bpy.context.active_object
        ow_body_link.name = ow_body_name
        ow_body_link.hide_render = True

        self.apply_transform_data(ow_body_link, ow_data["ground_body"]["transform"])
        ow_body_link.rotation_quaternion @= Quaternion((0, 1, 0), radians(90))

        return ow_body_link

    def set_compositor_nodes(self, scene: Scene, ow_data: OWSceneData):
        scene.use_nodes = True
        compositor_tree = scene.node_tree

        compositor_tree.nodes.clear()

        def init_render_layer_node(node: bpy.types.CompositorNodeRLayers):
            node.scene = scene

        def init_background_clip_node(node: bpy.types.CompositorNodeMovieClip):
            node.clip = bpy.data.movieclips['OW_mainCamera']

        def init_depth_clip_node(node: bpy.types.CompositorNodeMovieClip):
            depth_video_path = str(Path(self.filepath).parent.joinpath("depth.mp4"))
            node.clip = bpy.data.movieclips.load(depth_video_path)
            node.clip.name = 'OW_depth'

        def init_scale_node(node: bpy.types.CompositorNodeScale):
            node.space = "RENDER_SIZE"

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

        def build_value_node(value: float, label = "Value"):
            def init(node: bpy.types.CompositorNodeValue):
                node.label = label
                node.outputs["Value"].default_value = value

            return NodeBuilder(bpy.types.CompositorNodeValue, init=init)

        z_combine_node = NodeBuilder(bpy.types.CompositorNodeZcombine,
            _0=NodeBuilder(bpy.types.CompositorNodeExposure,
                Exposure=3,
                Image=(render_layers_node:=NodeBuilder(bpy.types.CompositorNodeRLayers,
                    init=init_render_layer_node,
                    output="Image",
                )),
            ),
            _1=render_layers_node.connect_output("Depth"),
            _2=NodeBuilder(bpy.types.CompositorNodeMovieClip,
                init=init_background_clip_node,
                output="Image",
            ),
            _3=build_math_node("DIVIDE",
                left=(
                    far_value_node:=build_value_node(ow_data["depth_camera"]["far_clip_plane"], label="far")
                ),
                right=build_math_node("ADD",
                    left=build_math_node("MULTIPLY",
                        left=build_math_node("SUBTRACT",
                            left=build_math_node("DIVIDE",
                                left=far_value_node,
                                right=build_value_node(ow_data["depth_camera"]["near_clip_plane"], label="near"),
                            ),
                            right=1,
                        ),
                        right=NodeBuilder(bpy.types.CompositorNodeDilateErode,
                            init=init_erode_node,
                            Mask=NodeBuilder(bpy.types.CompositorNodeSepRGBA,
                                output="R",
                                Image=NodeBuilder(bpy.types.CompositorNodeBlur,
                                    init=init_blur_node,
                                    Image=NodeBuilder(bpy.types.CompositorNodeScale,
                                        init=init_scale_node,
                                        Image=NodeBuilder(bpy.types.CompositorNodeMovieClip,
                                            init=init_depth_clip_node,
                                            output="Image",
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

        compositor_tree.links.new(z_combine_node.outputs["Image"], composite_node.inputs["Image"])
        compositor_tree.links.new(z_combine_node.outputs["Image"], viewer_node.inputs["Image"])

        arrange_nodes(compositor_tree)

    def set_world_hdri_nodes(self, scene: Scene, ow_data: OWSceneData):
        node_tree = scene.world.node_tree
        node_tree.nodes.clear()

        def init_environment_node(node: bpy.types.ShaderNodeTexEnvironment):
            hdri_video_path = str(Path(self.filepath).parent.joinpath("hdri.mp4"))

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

    def set_parent(self, children: Iterable[Object], parent: Object, *, keep_transform = True):
        for child in children:
            if child:
                child.select_set(state=True)

        bpy.context.view_layer.objects.active = parent

        bpy.ops.object.parent_set(type='OBJECT', keep_transform=keep_transform)

        for child in children:
            if child:
                child.select_set(state=False)
