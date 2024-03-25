import bpy
from bpy.types import Context, Event, Object

from ..api import APIClient, PostRecordingJson, PostSceneJson, Transform
from ..bpy_register import bpy_register
from ..properties import RecordingProperties, SceneProperties
from ..utils import GeneratorWithState
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

    def _run_async(self, context: Context):
        api_client = APIClient.from_context(context)

        recording_status = api_client.get_recording_status()

        if recording_status["inProgress"]:
            self.report({"ERROR"}, "recording is in progress")
            return {"CANCELLED"}

        scene = context.scene
        was_on_frame = scene.frame_current
        recording_props = RecordingProperties.from_context(context)
        scene_props = SceneProperties.from_context(context)
        frame_count = scene.frame_end - scene.frame_start + 1

        scene_json: PostSceneJson = {
            "origin": Transform.from_matrix(scene_props.origin_matrix).to_json(parent=scene_props.origin_parent),
            "hidePlayerModel": scene_props.hide_player_model,
        }

        if scene_creation_error := api_client.post_scene(scene_json):
            self.report({"ERROR"}, scene_creation_error["error"])
            return {"CANCELLED"}

        self._add_timer(context, recording_props.modal_timer_delay)

        recording_props.stage_progress = 0
        recording_props.is_recording = True

        # send animation data

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

        # record

        recording_json: PostRecordingJson = {
            "startFrame": scene.frame_start,
            "endFrame": scene.frame_end,
            "frameRate": scene.render.fps,
        }

        if not api_client.set_recorder_enabled(True):
            self.report({"ERROR"}, "failed to start recording")
            return {"CANCELLED"}

        recording_props.stage_description = "Recording"

        frames_recorded = GeneratorWithState(api_client.get_frames_recorded_async())

        for prev_count, current_count in iter_with_prev(frames_recorded):
            recording_props.stage_progress = current_count / frame_count

            if prev_count != current_count:
                recording_status = api_client.get_recorder_status()
                if not recording_status["enabled"]:
                    break

            yield {"TIMER"}

        if frames_recorded.returned == False:
            self.report({"ERROR"}, "failed to receive recorded frames count")
            return {"CANCELLED"}

        # end

        self.report({"INFO"}, "Outer Wilds render finished")

        return {"FINISHED"}

    def _after_event(self, context: Context, _: Event):
        context.area.tag_redraw()

    def _get_transform_local_to(self, parent: Object, child: Object) -> Transform:
        local_matrix = parent.matrix_world.inverted() @ child.matrix_world
        return Transform.from_matrix(local_matrix)

