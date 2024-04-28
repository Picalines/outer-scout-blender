from functools import partial
from math import radians
from operator import delitem
from typing import Callable

import bpy
from bpy.types import Camera, Context, Event, FCurve, Object
from bpy_extras.anim_utils import BakeOptions, bake_action
from mathutils import Matrix

from ..api import LEFT_HANDED_TO_RIGHT, RIGHT_HANDED_TO_LEFT, APIClient, Transform
from ..bpy_register import bpy_register
from ..properties import CameraProperties, ObjectProperties, SceneProperties, SceneRecordingProperties
from ..utils import Result, add_driver, defer, operator_do, with_defers
from .async_operator import AsyncOperator

ORIGIN_OBJECT_NAME = "scene.origin"


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
        recording_props = SceneRecordingProperties.from_context(context)

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

        defer(api_client.delete_scene)

        was_on_frame = scene.frame_current
        defer(scene.frame_set, was_on_frame)

        self._create_objects(context, api_client).then()

        self._send_keyframes(context, api_client).then()

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

        bpy.ops.outer_scout.import_assets()

    @Result.do()
    def _create_objects(self, context: Context, api_client: APIClient):
        scene = context.scene

        scene.frame_set(scene.frame_start)

        for object in scene.objects:
            object: Object
            object_props = ObjectProperties.of_object(object)

            if not object_props.has_unity_object_name:
                continue

            if object.type == "CAMERA" or object_props.object_type == "CUSTOM":
                object_matrix = object.matrix_world.copy()
                if object.type == "CAMERA":
                    object_matrix @= Matrix.Rotation(radians(-90), 4, "X")

                api_client.post_object(
                    name=object_props.unity_object_name,
                    transform=Transform.from_matrix(object_matrix).to_left(),
                    parent=ORIGIN_OBJECT_NAME,
                ).then()

            if object.type == "CAMERA":
                self._add_camera(context, api_client, object, object_props.unity_object_name).then()
            else:
                self._add_transform_recorder(api_client, object, object_props.unity_object_name).then()

    @Result.do()
    def _add_camera(self, context: Context, api_client: APIClient, object: Object, object_api_name: str):
        camera: Camera = object.data
        camera_props = CameraProperties.of_camera(camera)
        if not camera_props.is_active:
            return

        scene = context.scene

        match camera_props.outer_scout_type:
            case "PERSPECTIVE":
                camera.lens_unit = "MILLIMETERS"
                api_client.post_perspective_camera(
                    object_api_name,
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
                    object_api_name, {"faceResolution": camera_props.equirect_face_size}
                ).then()

            case not_implemented_camera_type:
                raise NotImplementedError(f"camera of type {not_implemented_camera_type} is not implemented")

        if camera_props.color_texture_props.has_recording_path:
            api_client.post_texture_recorder(object_api_name, "color", camera_props.color_texture_props).then()

        if camera_props.depth_texture_props.has_recording_path:
            api_client.post_texture_recorder(object_api_name, "depth", camera_props.depth_texture_props).then()

    @Result.do()
    def _add_transform_recorder(self, api_client: APIClient, object: Object, object_api_name: str):
        object_props = ObjectProperties.of_object(object)
        transform_props = object_props.transform_props

        if not transform_props.has_recording_path or transform_props.mode != "RECORD":
            return

        api_client.post_transform_recorder(
            object_api_name,
            {"format": "json", "outputPath": transform_props.absolute_recording_path, "origin": ORIGIN_OBJECT_NAME},
        ).then()

    @Result.do()
    @with_defers
    def _send_keyframes(self, context: Context, api_client: APIClient):
        scene = context.scene
        scene_props = SceneProperties.from_context(context)
        scene_frame_range = range(scene.frame_start, scene.frame_end + 1)

        vector_index_to_axis = {0: "x", 1: "y", 2: "z", 3: "w"}
        quaternion_index_to_axis = {0: "w", 1: "x", 2: "y", 3: "z"}  # order is converted for Unity

        scene_props_to_track = {"time.scale": "outer_scout_scene.time_scale"}

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

        ground_inverse_empty = add_temp_empty(context, "outer_scout.ground_inverse")
        if scene_props.has_ground_body:
            generate_inverted_transform_drivers(ground_inverse_empty, scene_props.ground_body)
        else:
            ground_inverse_empty.matrix_world = Matrix.Identity(4)

        camera_rotation_empty = add_temp_empty(
            context, "outer_scout.camera_rotation", matrix_world=Matrix.Rotation(radians(-90), 4, "X")
        )

        for object in scene.objects:
            object: Object
            object_props = ObjectProperties.of_object(object)

            if not (
                object is ground_inverse_empty
                or (
                    object_props.has_unity_object_name
                    and (object.type == "CAMERA" or object_props.transform_props.mode == "APPLY")
                )
            ):
                continue

            object_track_empty = add_temp_empty(
                context,
                (
                    f"outer_scout.object.{object_props.unity_object_name}"
                    if object_props.has_unity_object_name
                    else "outer_scout.scene.origin"
                ),
                matrix_world=RIGHT_HANDED_TO_LEFT,
            )

            camera_props = CameraProperties.of_camera(object.data) if object.type == "CAMERA" else None

            if camera_props and camera_props.is_active and camera_props.outer_scout_type in camera_props_to_track:
                for camera_prop, camera_prop_path in camera_props_to_track[camera_props.outer_scout_type].items():
                    object_track_empty[camera_prop] = 0.0
                    add_driver(object_track_empty, f'["{camera_prop}"]', "value", value=(object.data, camera_prop_path))

            # idea is to implement right_matrix_to_left using the Blender constraints
            add_multiply_transform_constraint(object_track_empty, object)

            if object.type == "CAMERA":
                # in Unity camera looks forward, but in Blender it looks down
                add_multiply_transform_constraint(object_track_empty, camera_rotation_empty)
            elif object is ground_inverse_empty:
                for scene_prop, scene_prop_path in scene_props_to_track.items():
                    object_track_empty[scene_prop] = 0.0
                    add_driver(object_track_empty, f'["{scene_prop}"]', "value", value=(scene, scene_prop_path))

            add_multiply_transform_constraint(object_track_empty, left_to_right_empty)

            track_action = bake_action(
                object_track_empty,
                action=None,
                frames=scene_frame_range,
                bake_options=BakeOptions(
                    only_selected=True,
                    do_pose=False,
                    do_object=True,
                    do_visual_keying=True,
                    do_constraint_clear=True,
                    do_parents_clear=True,
                    do_clean=True,
                    do_location=True,
                    do_rotation=True,
                    do_scale=False,
                    do_bbone=False,
                    do_custom_props=True,
                ),
            )

            defer(bpy.data.actions.remove, track_action, do_unlink=True)

            object_animation_properties_json = {}
            scene_animation_properties_json = {}

            for fcurve in track_action.fcurves:
                fcurve: FCurve

                match fcurve.data_path:
                    case "location":
                        outer_scout_property = "transform.position." + vector_index_to_axis[fcurve.array_index]
                        animation_properties_json = object_animation_properties_json
                    case "rotation_quaternion":
                        outer_scout_property = "transform.rotation." + quaternion_index_to_axis[fcurve.array_index]
                        animation_properties_json = object_animation_properties_json
                    case custom_data_path:
                        outer_scout_property = custom_data_path[2:-2]
                        animation_properties_json = (
                            scene_animation_properties_json
                            if outer_scout_property in scene_props_to_track
                            else object_animation_properties_json
                        )

                animation_properties_json[outer_scout_property] = {
                    "keyframes": {frame: {"value": fcurve.evaluate(frame)} for frame in scene_frame_range}
                }

            api_client.put_object_keyframes(
                ORIGIN_OBJECT_NAME if object is ground_inverse_empty else object_props.unity_object_name,
                {"properties": object_animation_properties_json},
            ).then()

            if len(scene_animation_properties_json):
                api_client.put_scene_keyframes({"properties": scene_animation_properties_json}).then()

    def _after_event(self, context: Context, _: Event):
        context.area.tag_redraw()


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


def generate_inverted_transform_drivers(object: Object, matrix_source: Object):
    inverted_loc_func_name = temp_driver_namespace_func("inverted_loc", lambda m: m.inverted().to_translation())
    inverted_rot_func_name = temp_driver_namespace_func("inverted_rot", lambda m: m.inverted().to_quaternion())

    matrix_var_name = "m"
    inverted_loc_expr = lambda i: f"{inverted_loc_func_name}({matrix_var_name})[{i}]"
    inverted_rot_expr = lambda i: f"{inverted_rot_func_name}({matrix_var_name})[{i}]"

    vars = {matrix_var_name: (matrix_source, "matrix_world")}

    for loc_i in range(3):
        add_driver(object, "location", inverted_loc_expr(loc_i), array_index=loc_i, **vars)

    for rot_i in range(4):
        add_driver(object, "rotation_quaternion", inverted_rot_expr(rot_i), array_index=rot_i, **vars)


def temp_driver_namespace_func(prefix: str, func: Callable, postfix="_"):
    func_name = prefix

    while func_name in bpy.app.driver_namespace:
        func_name += postfix

    bpy.app.driver_namespace[func_name] = func
    defer(delitem, bpy.app.driver_namespace, func_name)

    return func_name

