from functools import partial
from math import radians
from operator import delitem
from typing import Callable

import bpy
from bpy.path import abspath, clean_name
from bpy.types import ID, Camera, Context, Event, FCurve, Object
from mathutils import Matrix

from ..api import LEFT_HANDED_TO_RIGHT, RIGHT_HANDED_TO_LEFT, APIClient, Transform
from ..bpy_register import bpy_register
from ..properties import CameraProperties, RecordingProperties, SceneProperties
from ..utils import Result, defer, operator_do, with_defers
from .async_operator import AsyncOperator


@bpy_register
class RecordOperator(AsyncOperator):
    """Record footage from Outer Wilds and import it to current project"""

    bl_idname = "outer_scout.record"
    bl_label = "Record"

    @classmethod
    def poll(cls, context) -> bool:
        if not bpy.data.is_saved:
            cls.poll_message_set("Save project before recording")
            return False

        scene_props = SceneProperties.from_context(context)
        return scene_props.is_scene_created

    @operator_do
    @with_defers
    def _run_async(self, context):
        recording_props = RecordingProperties.from_context(context)

        if recording_props.in_progress:
            Result.do_error("recording is in progress")

        scene_props = SceneProperties.from_context(context)
        api_client = APIClient.from_context(context)
        scene = context.scene

        api_client.post_scene(
            {
                "origin": Transform.from_matrix(scene_props.origin_matrix).to_json(parent=scene_props.origin_parent),
                "hidePlayerModel": scene_props.hide_player_model,
            }
        ).then()

        was_on_frame = scene.frame_current
        defer(scene.frame_set, was_on_frame)

        self._create_cameras(context, api_client).then()

        self._send_scene_keyframes(context, api_client).then()

        self._send_camera_keyframes(context, api_client).then()

        api_client.post_scene_recording(
            {
                "startFrame": scene.frame_start,
                "endFrame": scene.frame_end,
                "frameRate": scene.render.fps,
            }
        ).then()

        recording_props.progress = 0
        recording_props.in_progress = True
        defer(setattr, recording_props, "in_progress", False)

        self._add_timer(context, recording_props.modal_timer_delay)

        frame_count = scene.frame_end - scene.frame_start + 1

        while recording_props.in_progress:
            recording_status = api_client.get_recording_status().then()

            recording_props.in_progress = recording_status["inProgress"]
            recording_props.progress = recording_status["framesRecorded"] / frame_count
            context.area.tag_redraw()

            yield {"TIMER"}

        api_client.delete_scene().then()

        self._reimport_camera_recordings(context)

    @Result.do()
    @with_defers
    def _create_cameras(self, context: Context, api_client: APIClient):
        scene = context.scene
        cameras: list[tuple[Object, Camera]] = [
            (camera_obj, camera_obj.data) for camera_obj in scene.objects if camera_obj.type == "CAMERA"
        ]

        scene.frame_set(scene.frame_start)

        for object, camera in cameras:
            camera_props = CameraProperties.of_camera(camera)
            if not camera_props.is_used_in_scene:
                continue

            object_name = get_camera_api_name(camera)

            camera_transform = Transform.from_matrix(object.matrix_world @ Matrix.Rotation(radians(-90), 4, "X"))

            api_client.post_object(name=object_name, transform=camera_transform.to_left()).then()

            match camera_props.outer_scout_type:
                case "PERSPECTIVE":
                    camera.lens_unit = "MILLIMETERS"
                    api_client.post_perspective_camera(
                        object_name,
                        {
                            "gateFit": get_camera_gate_fit(context, camera),
                            "resolution": {"width": scene.render.resolution_x, "height": scene.render.resolution_y},
                            "perspective": {
                                "focalLength": camera.lens,
                                "sensorSize": (camera.sensor_width, camera.sensor_height),
                                "lensShift": (camera.shift_x, camera.shift_y),
                                "nearClipPlane": camera.clip_start,
                                "farClipPlane": camera.clip_end,
                            },
                        },
                    ).then()

                case "EQUIRECTANGULAR":
                    api_client.post_equirect_camera(
                        object_name, {"faceResolution": camera_props.equirect_face_size}
                    ).then()

                case not_implemented_camera_type:
                    raise NotImplementedError(f"camera of type {not_implemented_camera_type} is not implemented")

            if camera_props.has_color_recording_path:
                api_client.post_texture_recorder(
                    object_name,
                    {
                        "property": "camera.renderTexture.color",
                        "outputPath": abspath(camera_props.color_recording_path),
                        "format": "mp4",
                        "constantRateFactor": 18,  # TODO: expose property
                    },
                ).then()

            if camera_props.has_depth_recording_path:
                api_client.post_texture_recorder(
                    object_name,
                    {
                        "property": "camera.renderTexture.depth",
                        "outputPath": abspath(camera_props.depth_recording_path),
                        "format": "mp4",
                        "constantRateFactor": 18,  # TODO: expose property
                    },
                ).then()

    @Result.do()
    @with_defers
    def _send_scene_keyframes(self, context: Context, api_client: APIClient):
        scene = context.scene
        scene_frame_range = range(scene.frame_start, scene.frame_end + 1)
        scene_props = SceneProperties.from_context(context)

        left_to_right_empty = add_temp_empty(context, "outer_scout.left_to_right", matrix_world=LEFT_HANDED_TO_RIGHT)

        ground_inverse_empty = add_temp_empty(context, "outer_scout.ground_inverse")
        generate_inverted_transform_drivers(ground_inverse_empty, scene_props.ground_body)

        bpy.ops.object.select_all(action="DESELECT")

        origin_empty = add_temp_empty(context, "outer_scout.scene.origin", matrix_world=RIGHT_HANDED_TO_LEFT)
        add_multiply_transform_constraint(origin_empty, ground_inverse_empty)
        add_multiply_transform_constraint(origin_empty, left_to_right_empty)

        scene_props_to_track = {"time.scale": "outer_scout_scene.time_scale"}

        for scene_prop, scene_prop_path in scene_props_to_track.items():
            origin_empty[scene_prop] = 0.0
            add_single_prop_driver(
                origin_empty,
                f'["{scene_prop}"]',
                target_id_type="SCENE",
                target_id=scene,
                target_data_path=scene_prop_path,
            )

        bpy.ops.nla.bake(
            frame_start=scene.frame_start,
            frame_end=scene.frame_end,
            only_selected=True,
            visual_keying=True,
            clear_constraints=True,
            bake_types={"OBJECT"},
            channel_types={"LOCATION", "ROTATION", "PROPS"},
        )

        track_action = origin_empty.animation_data.action
        defer(bpy.data.actions.remove, track_action, do_unlink=True)

        vector_index_to_axis = {0: "x", 1: "y", 2: "z", 3: "w"}
        quaternion_index_to_axis = {0: "w", 1: "x", 2: "y", 3: "z"}

        scene_animation_properties_json = {}
        origin_animation_properties_json = {}

        for fcurve in track_action.fcurves:
            fcurve: FCurve

            match fcurve.data_path:
                case "location":
                    outer_scout_property = "transform.position." + vector_index_to_axis[fcurve.array_index]
                    animation_properties_json = origin_animation_properties_json
                case "rotation_quaternion":
                    outer_scout_property = "transform.rotation." + quaternion_index_to_axis[fcurve.array_index]
                    animation_properties_json = origin_animation_properties_json
                case custom_data_path:
                    outer_scout_property = custom_data_path[2:-2]
                    animation_properties_json = scene_animation_properties_json

            animation_properties_json[outer_scout_property] = {
                "keyframes": {frame: {"value": fcurve.evaluate(frame)} for frame in scene_frame_range}
            }

        api_client.put_scene_keyframes({"properties": scene_animation_properties_json}).then()
        api_client.put_object_keyframes("scene.origin", {"properties": origin_animation_properties_json}).then()

    @Result.do()
    @with_defers
    def _send_camera_keyframes(self, context: Context, api_client: APIClient):
        scene = context.scene
        scene_frame_range = range(scene.frame_start, scene.frame_end + 1)

        cameras: list[tuple[Object, Camera]] = [
            (camera_obj, camera_obj.data) for camera_obj in scene.objects if camera_obj.type == "CAMERA"
        ]

        vector_index_to_axis = {0: "x", 1: "y", 2: "z", 3: "w"}
        quaternion_index_to_axis = {0: "w", 1: "x", 2: "y", 3: "z"}

        camera_props_to_track = {
            "PERSPECTIVE": {
                "camera.perspective.focalLength": "lens",
                "camera.perspective.sensorSize.x": "sensor_width",
                "camera.perspective.sensorSize.y": "sensor_height",
                "camera.perspective.lensShift.x": "shift_x",
                "camera.perspective.lensShift.y": "shift_y",
                "camera.perspective.nearClipPlane": "clip_start",
                "camera.perspective.farClipPlane": "clip_end",
            },
        }

        left_to_right_empty = add_temp_empty(context, "outer_scout.left_to_right", matrix_world=LEFT_HANDED_TO_RIGHT)

        camera_rotation_empty = add_temp_empty(
            context, "outer_scout.camera_rotation", matrix_world=Matrix.Rotation(radians(-90), 4, "X")
        )

        for camera_object, camera in cameras:
            camera_props = CameraProperties.of_camera(camera)
            if not camera_props.is_used_in_scene:
                continue

            object_name = get_camera_api_name(camera)

            bpy.ops.object.select_all(action="DESELECT")
            camera_empty = add_temp_empty(
                context, f"outer_scout.camera.{object_name}", matrix_world=RIGHT_HANDED_TO_LEFT
            )

            # idea is to implement right_matrix_to_left using the Blender constraints
            # and also add X rotation to the camera
            add_multiply_transform_constraint(camera_empty, camera_object)
            add_multiply_transform_constraint(camera_empty, camera_rotation_empty)
            add_multiply_transform_constraint(camera_empty, left_to_right_empty)

            if camera_props.outer_scout_type in camera_props_to_track:
                for camera_prop, camera_prop_path in camera_props_to_track[camera_props.outer_scout_type].items():
                    camera_empty[camera_prop] = 0.0
                    add_single_prop_driver(
                        camera_empty,
                        f'["{camera_prop}"]',
                        target_id_type="CAMERA",
                        target_id=camera,
                        target_data_path=camera_prop_path,
                    )

            bpy.ops.nla.bake(
                frame_start=scene.frame_start,
                frame_end=scene.frame_end,
                only_selected=True,
                visual_keying=True,
                clear_constraints=True,
                bake_types={"OBJECT"},
                channel_types={"LOCATION", "ROTATION", "PROPS"},
            )

            track_action = camera_empty.animation_data.action
            defer(bpy.data.actions.remove, track_action, do_unlink=True)

            animation_properties_json = {}

            for fcurve in track_action.fcurves:
                fcurve: FCurve

                match fcurve.data_path:
                    case "location":
                        outer_scout_property = "transform.position." + vector_index_to_axis[fcurve.array_index]
                    case "rotation_quaternion":
                        outer_scout_property = "transform.rotation." + quaternion_index_to_axis[fcurve.array_index]
                    case custom_data_path:
                        outer_scout_property = custom_data_path[2:-2]

                animation_properties_json[outer_scout_property] = {
                    "keyframes": {frame: {"value": fcurve.evaluate(frame)} for frame in scene_frame_range}
                }

            api_client.put_object_keyframes(object_name, {"properties": animation_properties_json}).then()

    def _reimport_camera_recordings(self, context: Context):
        scene = context.scene
        cameras: list[tuple[Object, Camera]] = [
            (camera_obj, camera_obj.data) for camera_obj in scene.objects if camera_obj.type == "CAMERA"
        ]

        for camera_object, camera in cameras:
            camera_props = CameraProperties.of_camera(camera)
            if not camera_props.is_used_in_scene:
                continue

            with context.temp_override(active_object=camera_object):
                bpy.ops.outer_scout.import_camera_recording()

    def _after_event(self, context: Context, _: Event):
        context.area.tag_redraw()


def get_camera_api_name(camera: Camera):
    return clean_name(camera.name)


def get_camera_gate_fit(context: Context, camera: Camera):
    match camera.sensor_fit:
        case "AUTO":
            render = context.scene.render
            return "horizontal" if render.resolution_x > render.resolution_y else "vertical"
        case "VERTICAL":
            return "vertical"
        case "HORIZONTAL":
            return "horizontal"


def add_temp_empty(
    context: Context, name: str, *, rotation_mode="QUATERNION", matrix_world: Matrix | None = None
) -> Object:
    bpy.ops.object.empty_add()
    empty: Object = context.active_object
    empty.name = name
    empty.rotation_mode = rotation_mode
    empty.matrix_world = matrix_world or Matrix.Identity(4)
    defer(bpy.data.objects.remove, empty, do_unlink=True)
    return empty


def add_transform_mix_constraint(object: Object, target: Object, *, mix_mode: str, type: str):
    constraint = object.constraints.new(type)

    constraint.target = target
    constraint.mix_mode = mix_mode

    return constraint


add_multiply_transform_constraint = partial(add_transform_mix_constraint, type="COPY_TRANSFORMS", mix_mode="AFTER_FULL")


def add_single_prop_driver(
    object: Object,
    data_path: str,
    *,
    target_id_type: str,
    target_id: ID,
    target_data_path: str,
    array_index=-1,
    var_name="v",
    expression: str | None = None,
):
    driver = object.driver_add(data_path, array_index).driver

    driver_var = driver.variables.new()
    driver_var.name = var_name
    driver_var.type = "SINGLE_PROP"
    driver_var.targets[0].id_type = target_id_type
    driver_var.targets[0].id = target_id
    driver_var.targets[0].data_path = target_data_path
    driver.expression = expression or driver_var.name

    return driver


def generate_inverted_transform_drivers(object: Object, matrix_source: Object):
    inverted_loc_func_name = temp_driver_namespace_func("inverted_loc", lambda m: m.inverted().to_translation())
    inverted_rot_func_name = temp_driver_namespace_func("inverted_rot", lambda m: m.inverted().to_quaternion())

    matrix_var_name = "m"
    inverted_loc_expr = lambda i: f"{inverted_loc_func_name}({matrix_var_name})[{i}]"
    inverted_rot_expr = lambda i: f"{inverted_rot_func_name}({matrix_var_name})[{i}]"

    for loc_i in range(3):
        add_single_prop_driver(
            object,
            "location",
            array_index=loc_i,
            target_id_type="OBJECT",
            target_id=matrix_source,
            target_data_path="matrix_world",
            var_name=matrix_var_name,
            expression=inverted_loc_expr(loc_i),
        )

    for rot_i in range(4):
        add_single_prop_driver(
            object,
            "rotation_quaternion",
            array_index=rot_i,
            target_id_type="OBJECT",
            target_id=matrix_source,
            target_data_path="matrix_world",
            var_name=matrix_var_name,
            expression=inverted_rot_expr(rot_i),
        )


def temp_driver_namespace_func(prefix: str, func: Callable, postfix="_"):
    func_name = prefix

    while func_name in bpy.app.driver_namespace:
        func_name += postfix

    bpy.app.driver_namespace[func_name] = func
    defer(delitem, bpy.app.driver_namespace, func_name)

    return func_name

