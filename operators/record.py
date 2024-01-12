from os import makedirs

import bpy
from bpy.types import Context, Event, Object

from ..api import APIClient
from ..api.models import RecorderSettingsDTO, TransformDTO, get_camera_dto
from ..bpy_register import bpy_register
from ..preferences import OWRecorderPreferences
from ..properties import OWRecorderProperties, OWRecorderReferenceProperties, OWRecorderSceneProperties
from ..utils import GeneratorWithState, get_footage_path, iter_with_prev
from .async_operator import AsyncOperator


@bpy_register
class OW_RECORDER_OT_record(AsyncOperator):
    """Record footage from Outer Wilds and import it to current project (save project before running)"""

    bl_idname = "ow_recorder.record"
    bl_label = "Record"

    _timer = None

    @classmethod
    def poll(cls, context) -> bool:
        reference_props = OWRecorderReferenceProperties.from_context(context)
        return all(
            (
                bpy.data.is_saved,
                context.scene.camera,
                reference_props.ground_body,
                reference_props.hdri_pivot,
            )
        )

    def _run_async(self, context: Context):
        api_client = APIClient(OWRecorderPreferences.from_context(context))

        recorder_status = api_client.get_recorder_status()

        if recorder_status["enabled"]:
            self.report({"ERROR"}, "already recording")
            return {"CANCELLED"}

        scene = context.scene

        was_on_frame = scene.frame_current

        recorder_props = OWRecorderProperties.from_context(context)
        scene_props = OWRecorderSceneProperties.from_context(context)
        ref_props = OWRecorderReferenceProperties.from_context(context)

        frame_count = scene.frame_end - scene.frame_start + 1

        footage_path = get_footage_path(context)
        makedirs(footage_path, exist_ok=True)

        recorder_settings: RecorderSettingsDTO = {
            "outputDirectory": footage_path,
            "startFrame": scene.frame_start,
            "endFrame": scene.frame_end,
            "frameRate": scene.render.fps,
            "resolutionX": scene.render.resolution_x,
            "resolutionY": scene.render.resolution_y,
            "recordHdri": recorder_props.record_hdri,
            "recordDepth": recorder_props.record_depth,
            "hdriFaceSize": recorder_props.hdri_face_size,
            "hidePlayerModel": recorder_props.hide_player_model,
        }

        if not api_client.set_recorder_settings(recorder_settings):
            self.report({"ERROR"}, "failed to set recorder settings")
            return {"CANCELLED"}

        recorder_status = api_client.get_recorder_status()

        if not recorder_status["isAbleToRecord"]:
            self.report({"ERROR"}, "unable to record")
            return {"CANCELLED"}

        self._timer = context.window_manager.event_timer_add(recorder_props.modal_timer_delay, window=context.window)

        recorder_props.stage_progress = 0
        recorder_props.is_recording = True

        # send animation data

        ground_body: Object = ref_props.ground_body
        hdri_pivot: Object = ref_props.hdri_pivot
        camera = scene.camera

        recorder_props.stage_description = "Sending animation"

        max_chunk_size = recorder_props.animation_chunk_size

        chunk_keyframe_values: dict[str, list] = {
            prop_name: [None] * max_chunk_size
            for prop_name in (
                "free-camera/transform",
                *(("hdri-pivot/transform",) if recorder_props.record_hdri else ()),
                "free-camera/camera-info",
                "time/scale",
            )
        }

        animated_transform_objects = {
            "free-camera/transform": camera,
            **({"hdri-pivot/transform": hdri_pivot} if recorder_props.record_hdri else {}),
        }

        scene.frame_set(frame=scene.frame_start)

        while True:
            frame_number = scene.frame_current - scene.frame_start + 1
            recorder_props.stage_progress = frame_number / frame_count

            current_chunk_size = 0
            chunk_start_frame = scene.frame_current
            at_end = False

            for chunk_frame_offset in range(max_chunk_size):
                scene.frame_set(frame=chunk_start_frame + chunk_frame_offset)
                current_chunk_size += 1

                for prop_api_name, transform_object in animated_transform_objects.items():
                    local_matrix = ground_body.matrix_world.inverted() @ transform_object.matrix_world
                    local_transform = TransformDTO.from_matrix(local_matrix)
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

        if not api_client.set_recorder_enabled(True):
            self.report({"ERROR"}, "failed to start recording")
            return {"CANCELLED"}

        recorder_props.stage_description = "Recording"

        frames_recorded = GeneratorWithState(api_client.get_frames_recorded_async())

        for prev_count, current_count in iter_with_prev(frames_recorded):
            recorder_props.stage_progress = current_count / frame_count

            if prev_count != current_count:
                recorder_status = api_client.get_recorder_status()
                if not recorder_status["enabled"]:
                    break

            yield {"TIMER"}

        if frames_recorded.returned == False:
            self._remove_timer(context)
            self.report({"ERROR"}, "failed to receive recorded frames count")
            return {"CANCELLED"}

        # end

        self._remove_timer(context)
        self.report({"INFO"}, "Outer Wilds render finished")

        return {"FINISHED"}

    def _after_event(self, context: Context, _: Event):
        context.area.tag_redraw()

    def _remove_timer(self, context: Context):
        recorder_props = OWRecorderProperties.from_context(context)

        context.window_manager.event_timer_remove(self._timer)
        recorder_props.is_recording = False

    def _get_transform_local_to(self, parent: Object, child: Object) -> TransformDTO:
        local_matrix = parent.matrix_world.inverted() @ child.matrix_world
        return TransformDTO.from_matrix(local_matrix)

