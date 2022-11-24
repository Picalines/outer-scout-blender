import os
from pathlib import Path
from math import radians

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator, Object, Camera, Scene
from mathutils import Vector, Quaternion, Euler

from .node_utils import arrange_nodes, NodeBuilder, create_node
from .ow_scene_data import OWSceneData, load_ow_scene_data


class OWSceneImporter(Operator, ImportHelper):
    bl_idname = "outer_wilds_recorder.importer"
    bl_label = "Import .owscene"

    filename_ext = ".owscene"

    filter_glob : StringProperty(
        default = "*.owscene",
        options = { 'HIDDEN' },
        maxlen= 255
    )

    ow_bodies_folder : StringProperty(
        name = "Outer Wilds bodies (planets) folder",
        description = "test",
        default = "D:\\Projects\\Blender\\_owBodies\\",
        subtype = "DIR_PATH",
    )

    def execute(self, _):
        current_scene = bpy.context.scene

        ow_data = load_ow_scene_data(self.filepath)

        if ow_data["body"]["name"] in bpy.data.objects:
            self.report({"ERROR"}, "create new project before importing OW scene!")
            return {"CANCELED"}

        # create OW body
        ow_body = self.load_ow_body(ow_data)
        if ow_body is None:
            self.report({"ERROR"}, f"couldn't load .blend file of '{ow_data['body']['name']}'")
            return {"CANCELED"}

        ow_body.rotation_mode = 'QUATERNION'
        ow_body.rotation_quaternion = Quaternion(ow_data["body"]["transform"]["rotation"]) @ Quaternion((0, 1, 0), radians(90))

        # create body pivot
        bpy.ops.object.empty_add()
        ow_body_pivot = bpy.context.active_object
        ow_body_pivot.name = ow_data["body"]["name"] + '_Pivot'
        ow_body_pivot.location = Vector(ow_data["player"]["transform"]["position"]) - Vector(ow_data["body"]["transform"]["position"])
        ow_body_pivot.rotation_mode = 'QUATERNION'
        ow_body_pivot.rotation_quaternion = Quaternion(ow_data["player"]["transform"]["rotation"])

        # create player camera pivot
        bpy.ops.object.empty_add()
        player_camera_pivot = bpy.context.active_object
        player_camera_pivot.name = 'PlayerCamera_Pivot'
        player_camera_pivot.location = Vector(ow_data["player_camera"]["transform"]["position"]) - Vector(ow_data["body"]["transform"]["position"])
        player_camera_pivot.rotation_mode = 'QUATERNION'
        player_camera_pivot.rotation_quaternion = Quaternion(ow_data["player_camera"]["transform"]["rotation"])

        # create camera
        camera = self.create_camera(current_scene, ow_data)

        # move scene to origin
        self.set_parent([ow_body, camera, player_camera_pivot], ow_body_pivot, keep_transform=True)
        ow_body_pivot.location = (0, 0, 0)

        # make X - right, Y - forward, Z - up
        # (like in new General project)
        ow_body_pivot.rotation_mode = 'XYZ'
        ow_body_pivot.rotation_euler = Euler((radians(90), 0, radians(90)), 'XYZ')

        # make ow_body not selectable
        ow_body.hide_select = True

        # scene properties
        current_scene.frame_end = ow_data["frames"]
        current_scene.render.fps = 60
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
        camera.location = Vector(ow_data["background_camera"]["transform"]["position"]) - Vector(ow_data["body"]["transform"]["position"])
        camera.rotation_mode = 'QUATERNION'
        camera.rotation_quaternion = Quaternion(ow_data["background_camera"]["transform"]["rotation"]) @ Quaternion((0, 1, 0), -radians(90))

        return camera

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

        def init_scale_node(node: bpy.types.CompositorNodeScale):
            node.space = "RENDER_SIZE"

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
                        right=NodeBuilder(bpy.types.CompositorNodeSepRGBA,
                            output=0,
                            Image=NodeBuilder(bpy.types.CompositorNodeBlur,
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
            node.image_user.frame_duration = ow_data["frames"]
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

    def load_ow_body(self, ow_data: OWSceneData) -> Object | None:
        ow_body_name = ow_data["body"]["name"]

        ow_body_project_path = os.path.join(self.ow_bodies_folder, ow_body_name + ".blend")
        ow_body_project_import_status = bpy.ops.wm.link(
            filepath=os.path.join(ow_body_project_path, "Collection", "Collection"),
            filename="Collection",
            directory=os.path.join(ow_body_project_path, "Collection"))

        if ow_body_project_import_status != {"FINISHED"}:
            return None

        ow_body_link = bpy.context.active_object
        ow_body_link.name = ow_body_name
        ow_body_link.hide_render = True

        return ow_body_link

    def set_parent(self, children: list[Object], parent: Object, *, keep_transform = True):
        for child in children:
            child.select_set(state=True)

        bpy.context.view_layer.objects.active = parent

        bpy.ops.object.parent_set(type='OBJECT', keep_transform=keep_transform)

        for child in children:
            child.select_set(state=False)
