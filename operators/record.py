from math import radians

import bpy
from bpy.path import abspath, clean_name
from bpy.types import Camera, Context, Event, Object
from mathutils import Matrix

from ..api import APIClient, Transform
from ..bpy_register import bpy_register
from ..properties import CameraProperties, RecordingProperties, SceneProperties
from ..utils import Result, operator_do
from .async_operator import AsyncOperator


def get_camera_gate_fit(context: Context, camera: Camera):
    match camera.sensor_fit:
        case "AUTO":
            render = context.scene.render
            return "horizontal" if render.resolution_x > render.resolution_y else "vertical"
        case "VERTICAL":
            return "vertical"
        case "HORIZONTAL":
            return "horizontal"


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

        # send animation data

        # self._send_keyframes(context, api_client).then()

        # record

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

        for object, camera in cameras:
            camera_props = CameraProperties.of_camera(camera)
            if camera_props.outer_scout_type == "NONE":
                continue

            object_name = clean_name(camera.name)

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
    def _send_keyframes(self, context: Context, api_client: APIClient):
        scene = context.scene
        was_on_frame = scene.frame_current
        frame_count = scene.frame_end - scene.frame_start + 1

        ground_body: Object = ref_props.ground_body
        hdri_pivot: Object = ref_props.hdri_pivot
        camera = scene.camera

        recording_props.stage_description = "Sending animation"

        max_chunk_size = recording_props.animation_chunk_size

        chunk_keyframe_values: dict[str, list] = {
            prop_name: [None] * max_chunk_size
            for prop_name in (
                "free-camera/transform",
                *(("hdri-pivot/transform",) if recording_props.record_hdri else ()),
                "free-camera/camera-info",
                "time/scale",
            )
        }

        animated_transform_objects = {
            "free-camera/transform": camera,
            **({"hdri-pivot/transform": hdri_pivot} if recording_props.record_hdri else {}),
        }

        scene.frame_set(frame=scene.frame_start)

        while True:
            frame_number = scene.frame_current - scene.frame_start + 1
            recording_props.stage_progress = frame_number / frame_count

            current_chunk_size = 0
            chunk_start_frame = scene.frame_current
            at_end = False

            for chunk_frame_offset in range(max_chunk_size):
                scene.frame_set(frame=chunk_start_frame + chunk_frame_offset)
                current_chunk_size += 1

                for prop_api_name, transform_object in animated_transform_objects.items():
                    local_matrix = ground_body.matrix_world.inverted() @ transform_object.matrix_world
                    local_transform = Transform.from_matrix(local_matrix)
                    transform_keyframe = local_transform.blender_to_unity().to_json()

                    chunk_keyframe_values[prop_api_name][chunk_frame_offset] = transform_keyframe

                chunk_keyframe_values["free-camera/camera-info"][chunk_frame_offset] = get_camera_dto(camera.data)

                chunk_keyframe_values["time/scale"][chunk_frame_offset] = scene_props.time_scale

                if scene.frame_current >= scene.frame_end:
                    at_end = True
                    break

            for prop_api_name, keyframe_values in chunk_keyframe_values.items():
                keyframe_values = keyframe_values[:current_chunk_size]
                success = api_client.set_keyframes(prop_api_name, chunk_start_frame, keyframe_values)

                if not success:
                    self.report(
                        {"WARNING"},
                        f"failed to send animation {prop_api_name} data at frame {chunk_start_frame}",
                    )

            if at_end:
                break

            yield {"TIMER"}

        scene.frame_set(frame=was_on_frame)

    def _after_event(self, context: Context, _: Event):
        context.area.tag_redraw()

    def _get_transform_local_to(self, parent: Object, child: Object) -> Transform:
        local_matrix = parent.matrix_world.inverted() @ child.matrix_world
        return Transform.from_matrix(local_matrix)

