from math import radians

import bpy
from bpy.path import abspath, clean_name
from bpy.types import ID, Camera, Context, CopyTransformsConstraint, Event, FCurve, Object
from mathutils import Matrix

from ..api import LEFT_HANDED_TO_RIGHT, RIGHT_HANDED_TO_LEFT, APIClient, Transform
from ..bpy_register import bpy_register
from ..properties import CameraProperties, RecordingProperties, SceneProperties
from ..utils import Result, operator_do
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

        self._create_cameras(context, api_client).then()

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

        self._add_timer(context, recording_props.modal_timer_delay)

        frame_count = scene.frame_end - scene.frame_start + 1

        while recording_props.in_progress:
            recording_status = api_client.get_recording_status().then()

            recording_props.in_progress = recording_status["inProgress"]
            recording_props.progress = recording_status["framesRecorded"] / frame_count
            context.area.tag_redraw()

            yield {"TIMER"}

        recording_props.in_progress = False

        self.report({"INFO"}, "recording finished")

    @Result.do()
    def _create_cameras(self, context: Context, api_client: APIClient):
        scene = context.scene
        cameras: list[tuple[Object, Camera]] = [
            (camera_obj, camera_obj.data) for camera_obj in scene.objects if camera_obj.type == "CAMERA"
        ]

        scene.frame_set(scene.frame_start)

        for object, camera in cameras:
            camera_props = CameraProperties.of_camera(camera)
            if camera_props.outer_scout_type == "NONE":
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

            if camera_props.is_recording_color:
                api_client.post_texture_recorder(
                    object_name,
                    {
                        "property": "camera.renderTexture.color",
                        "outputPath": abspath(camera_props.color_recording_path),
                        "format": "mp4",
                        "constantRateFactor": 18,  # TODO: expose property
                    },
                ).then()

            if camera_props.is_recording_depth:
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
            "EQUIRECTANGULAR": {},
        }

        bpy.ops.object.empty_add()
        left_to_right_empty: Object = context.active_object
        left_to_right_empty.matrix_world = LEFT_HANDED_TO_RIGHT
        left_to_right_empty.name = "outer_scout.left_to_right_empty"

        bpy.ops.object.empty_add()
        camera_rotation_empty: Object = context.active_object
        camera_rotation_empty.matrix_world = Matrix.Rotation(radians(-90), 4, "X")
        camera_rotation_empty.name = "outer_scout.camera_rotation"

        try:
            for camera_object, camera in cameras:
                camera_props = CameraProperties.of_camera(camera)
                if camera_props.outer_scout_type == "NONE":
                    continue

                object_name = get_camera_api_name(camera)

                bpy.ops.object.select_all(action="DESELECT")
                bpy.ops.object.empty_add()
                camera_track_empty: Object = context.active_object
                camera_track_empty.name = f"outer_scout.{object_name}.track"
                camera_track_empty.rotation_mode = "QUATERNION"

                # idea is to implement right_matrix_to_left using the Blender constraints
                # and also add X rotation to the camera
                camera_track_empty.matrix_world = RIGHT_HANDED_TO_LEFT
                add_copy_transform_constraint(camera_track_empty, camera_object, mix_mode="AFTER_FULL")
                add_copy_transform_constraint(camera_track_empty, camera_rotation_empty, mix_mode="AFTER_FULL")
                add_copy_transform_constraint(camera_track_empty, left_to_right_empty, mix_mode="AFTER_FULL")

                for camera_prop, camera_prop_path in camera_props_to_track[camera_props.outer_scout_type].items():
                    camera_track_empty[camera_prop] = 0.0
                    add_single_prop_copy_driver(
                        camera_track_empty,
                        f'["{camera_prop}"]',
                        target_id_type="CAMERA",
                        target_id=camera,
                        target_data_path=camera_prop_path,
                    )

                bpy.ops.nla.bake(
                    frame_start=scene.frame_start,
                    frame_end=scene.frame_end,
                    step=1,
                    only_selected=True,
                    visual_keying=True,
                    clear_constraints=True,
                    clean_curves=True,
                    bake_types={"OBJECT"},
                    channel_types={"LOCATION", "ROTATION", "SCALE", "PROPS"},
                )

                track_action = camera_track_empty.animation_data.action

                animation_properties_json = {}

                for fcurve in track_action.fcurves:
                    fcurve: FCurve

                    match fcurve.data_path:
                        case "location":
                            outer_scout_property = "transform.position." + vector_index_to_axis[fcurve.array_index]
                        case "rotation_quaternion":
                            outer_scout_property = "transform.rotation." + quaternion_index_to_axis[fcurve.array_index]
                        case "scale":
                            outer_scout_property = "transform.scale." + vector_index_to_axis[fcurve.array_index]
                        case custom_data_path:
                            outer_scout_property = custom_data_path[2:-2]

                    animation_properties_json[outer_scout_property] = {
                        "keyframes": {frame: {"value": fcurve.evaluate(frame)} for frame in scene_frame_range}
                    }

                try:
                    api_client.put_keyframes(object_name, {"properties": animation_properties_json}).then()
                finally:
                    bpy.data.actions.remove(track_action, do_unlink=True)
                    bpy.data.objects.remove(camera_track_empty, do_unlink=True)
        finally:
            bpy.data.objects.remove(left_to_right_empty, do_unlink=True)
            bpy.data.objects.remove(camera_rotation_empty, do_unlink=True)

    def _after_event(self, context: Context, _: Event):
        context.area.tag_redraw()

    def _get_transform_local_to(self, parent: Object, child: Object) -> Transform:
        local_matrix = parent.matrix_world.inverted() @ child.matrix_world
        return Transform.from_matrix(local_matrix)


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


def add_copy_transform_constraint(object: Object, target: Object, *, mix_mode: str):
    constraint: CopyTransformsConstraint = object.constraints.new("COPY_TRANSFORMS")

    constraint.target = target
    constraint.mix_mode = mix_mode

    return constraint


def add_single_prop_copy_driver(
    object: Object,
    data_path: str,
    *,
    target_id_type: str,
    target_id: ID,
    target_data_path: str,
    array_index=-1,
    var_name="v",
):
    driver = object.driver_add(data_path, array_index).driver

    driver_var = driver.variables.new()
    driver_var.name = var_name
    driver_var.type = "SINGLE_PROP"
    driver_var.targets[0].id_type = target_id_type
    driver_var.targets[0].id = target_id
    driver_var.targets[0].data_path = target_data_path
    driver.expression = driver_var.name

    return driver

