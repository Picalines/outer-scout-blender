from os import makedirs

import bpy
from bpy.types import Context, Event, Object

from ..bpy_register import bpy_register
from ..preferences import OWRecorderPreferences
from ..properties import (
    OWRecorderRenderProperties,
    OWRecorderSceneProperties,
    OWRecorderReferenceProperties,
)
from ..utils import GeneratorWithState, get_footage_path
from ..api.models import RecorderSettings, TransformModel, camera_info_from_blender
from ..api import APIClient

from .async_operator import AsyncOperator


@bpy_register
class OW_RECORDER_OT_render(AsyncOperator):
    """Render footage in Outer Wilds and import it to current project"""

    bl_idname = "ow_recorder.render"
    bl_label = "Render"

    _timer = None

    _render_props: OWRecorderRenderProperties = None

    @classmethod
    def poll(cls, context) -> bool:
        reference_props = OWRecorderReferenceProperties.from_context(context)
        return all(
            (
                context.scene.camera,
                reference_props.ground_body,
                reference_props.hdri_pivot,
            )
        )

    def _run_async(self, context: Context):
        api_client = APIClient(OWRecorderPreferences.from_context(context))

        if api_client.get_is_recording():
            self.report({"ERROR"}, "already recording")
            return {"CANCELLED"}

        scene = context.scene

        was_on_frame = scene.frame_current

        render_props = OWRecorderRenderProperties.from_context(context)
        scene_props = OWRecorderSceneProperties.from_context(context)
        ref_props = OWRecorderReferenceProperties.from_context(context)

        self._render_props = render_props

        frame_count = scene.frame_end - scene.frame_start + 1

        footage_path = get_footage_path(context)
        makedirs(footage_path, exist_ok=True)

        recorder_settings: RecorderSettings = {
            "output_directory": footage_path,
            "start_frame": scene.frame_start,
            "end_frame": scene.frame_end,
            "frame_rate": scene.render.fps,
            "resolution_x": scene.render.resolution_x,
            "resolution_y": scene.render.resolution_y,
            "record_hdri": render_props.record_hdri,
            "record_depth": render_props.record_depth,
            "hdri_face_size": render_props.hdri_face_size,
            "hide_player_model": render_props.hide_player_model,
            "show_progress_gui": render_props.show_progress_gui,
        }

        if not api_client.set_recorder_settings(recorder_settings):
            self.report({"ERROR"}, "failed to set recorder settings")
            return {"CANCELLED"}

        if not api_client.get_is_able_to_record():
            self.report({"ERROR"}, "unable to record")
            return {"CANCELLED"}

        self._timer = context.window_manager.event_timer_add(render_props.render_timer_delay, window=context.window)

        scene.frame_set(frame=scene.frame_start)
        render_props.render_stage_progress = 0

        render_props.is_rendering = True

        # send animation data

        ground_body: Object = ref_props.ground_body
        hdri_pivot: Object = ref_props.hdri_pivot
        camera = scene.camera

        render_props.render_stage_description = "Sending animation"

        animation_values: dict[str, list] = {
            name: []
            for name in (
                "free_camera/transform",
                "free_camera/camera_info",
                "time/scale",
                *(("hdri_pivot/transform",) if render_props.record_hdri else ()),
            )
        }

        animation_name_to_object = {
            "free_camera/transform": camera,
            **({"hdri_pivot/transform": hdri_pivot} if render_props.record_hdri else {}),
        }

        while True:
            frame_number = scene.frame_current - scene.frame_start + 1
            render_props.render_stage_progress = frame_number / frame_count

            chunk_start_frame = scene.frame_current
            at_end = False

            for chunk_frame_offset in range(render_props.animation_chunk_size):
                scene.frame_set(frame=chunk_start_frame + chunk_frame_offset)

                for animation_name, object in animation_name_to_object.items():
                    animation_values[animation_name].append(
                        self._get_transform_local_to(ground_body, object).blender_to_unity().to_json()
                    )

                animation_values["free_camera/camera_info"].append(camera_info_from_blender(camera.data))

                animation_values["time/scale"].append(scene_props.time_scale)

                if scene.frame_current >= scene.frame_end:
                    at_end = True
                    break

            for animation_name, frame_values in animation_values.items():
                success = api_client.set_animation_values_from_frame(animation_name, chunk_start_frame, frame_values)

                frame_values.clear()

                if not success:
                    self.report(
                        {"WARNING"},
                        f"failed to send animation {animation_name} data at frame {chunk_start_frame}",
                    )

            if at_end:
                break

            yield {"TIMER"}

        scene.frame_set(frame=was_on_frame)

        # render

        if not api_client.set_is_recording(True):
            self.report({"ERROR"}, "failed to start recording")
            return {"CANCELLED"}

        render_props.render_stage_description = "Rendering"

        frames_recorded = GeneratorWithState(api_client.get_frames_recorded_async())

        for count in frames_recorded:
            render_props.render_stage_progress = count / frame_count
            yield {"TIMER"}

        if frames_recorded.returned == False:
            self._remove_timer(context)
            self.report({"ERROR"}, "failed to receive recorded frames count")
            return {"CANCELLED"}

        # end

        self._remove_timer(context)
        self.report({"INFO"}, "Outer Wilds render finished")

        bpy.ops.ow_recorder.load_camera_background()
        bpy.ops.ow_recorder.generate_world_nodes()
        bpy.ops.ow_recorder.generate_compositor_nodes()

        return {"FINISHED"}

    def _after_event(self, context: Context, event: Event):
        context.area.tag_redraw()

    def _remove_timer(self, context: Context):
        context.window_manager.event_timer_remove(self._timer)
        self._render_props.is_rendering = False

    def _get_transform_local_to(self, parent: Object, child: Object) -> TransformModel:
        local_matrix = parent.matrix_world.inverted() @ child.matrix_world
        return TransformModel.from_matrix(local_matrix)
