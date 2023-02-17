from typing import Literal

import bpy
from bpy.types import Operator, Context, Event, Object
from bpy.path import abspath as bpy_abspath

from ..bpy_register import bpy_register
from ..ow_objects import get_current_ground_body, get_current_hdri_pivot
from ..preferences import OWRecorderPreferences
from ..properties import OWRecorderRenderProperties, OWRecorderSceneProperties
from ..api.models import RecorderSettings, TransformModel, camera_info_from_blender
from ..api import APIClient


@bpy_register
class OW_RECORDER_OT_render(Operator):
    """Render footage in Outer Wilds and import it to current project"""

    bl_idname = "ow_recorder.render"
    bl_label = "Render"

    _timer = None
    _api_client: APIClient = None
    _was_on_frame: int = 0
    _frame_count: int = 0
    _render_props: OWRecorderRenderProperties = None
    _scene_props: OWRecorderSceneProperties = None
    _stage: Literal["SENDING_ANIMATION", "RENDERING"] = ""

    @classmethod
    def poll(cls, context) -> bool:
        return all((context.scene.camera, get_current_ground_body()))

    def invoke(self, context: Context, _):
        self._api_client = APIClient(OWRecorderPreferences.from_context(context))

        if self._api_client.get_is_recording():
            self.report({"ERROR"}, "already recording")
            return {"CANCELLED"}

        scene = context.scene

        self._was_on_frame = scene.frame_current

        self._render_props = OWRecorderRenderProperties.from_context(context)
        self._scene_props = OWRecorderSceneProperties.from_context(context)

        self._frame_count = scene.frame_end - scene.frame_start + 1

        recorder_settings: RecorderSettings = {
            "output_directory": bpy_abspath("//Outer Wilds/footage/"),
            "start_frame": scene.frame_start,
            "end_frame": scene.frame_end,
            "frame_rate": scene.render.fps,
            "resolution_x": scene.render.resolution_x,
            "resolution_y": scene.render.resolution_y,
            "hdri_face_size": self._render_props.hdri_face_size,
            "hide_player_model": self._render_props.hide_player_model,
        }

        if not self._api_client.set_recorder_settings(recorder_settings):
            self.report({"ERROR"}, "failed to set recorder settings")
            return {"CANCELLED"}

        if not self._api_client.get_is_able_to_record():
            self.report({"ERROR"}, "unable to record")
            return {"CANCELLED"}

        self._timer = context.window_manager.event_timer_add(
            self._render_props.render_timer_delay, window=context.window
        )

        context.window_manager.modal_handler_add(self)

        scene.frame_set(frame=scene.frame_start)
        self._stage = "SENDING_ANIMATION"

        self._render_props.is_rendering = True

        return {"RUNNING_MODAL"}

    def modal(self, context: Context, event: Event):
        if event.type != "TIMER":
            return {"RUNNING_MODAL"}

        context.area.tag_redraw()

        self._render_props.is_rendering = True

        if self._stage == "SENDING_ANIMATION":
            result = self._stage_sending_animation(context)
        elif self._stage == "RENDERING":
            result = self._stage_rendering(context)
        else:
            raise NotImplemented

        if result != {"RUNNING_MODAL"}:
            self._render_props.is_rendering = False

        return result

    def _stage_sending_animation(self, context: Context):
        scene = context.scene

        self._render_props.render_stage_description = "Sending animation"

        frame_start = scene.frame_start
        frame_end = scene.frame_end

        frame_number = scene.frame_current - frame_start + 1
        self._render_props.render_stage_progress = frame_number / self._frame_count

        ground_body = get_current_ground_body()
        camera = scene.camera

        animation_values: dict[str, list] = {
            name: []
            for name in (
                "free_camera/transform",
                "free_camera/camera_info",
                "hdri_pivot/transform",
                "time/scale",
            )
        }

        animation_name_to_object = {
            "free_camera/transform": camera,
            "hdri_pivot/transform": get_current_hdri_pivot(),
        }

        chunk_start_frame = scene.frame_current
        at_end = False

        for chunk_frame_offset in range(self._render_props.animation_chunk_size):
            scene.frame_set(frame=chunk_start_frame + chunk_frame_offset)

            for animation_name, object in animation_name_to_object.items():
                animation_values[animation_name].append(
                    self._get_transform_local_to(ground_body, object)
                    .blender_to_unity()
                    .to_json()
                )

            animation_values["free_camera/camera_info"].append(
                camera_info_from_blender(camera.data)
            )

            animation_values["time/scale"].append(self._scene_props.time_scale)

            if scene.frame_current >= frame_end:
                at_end = True
                break

        for animation_name, frame_values in animation_values.items():
            success = self._api_client.set_animation_values_from_frame(
                animation_name, chunk_start_frame, frame_values
            )
            if not success:
                self.report(
                    {"WARNING"},
                    f"failed to send animation {animation_name} data at frame {chunk_start_frame}",
                )

        if at_end:
            if not self._api_client.set_is_recording(True):
                self.report({"ERROR"}, "failed to start recording")
                return {"CANCELLED"}

            self._stage = "RENDERING"
            scene.frame_set(frame=self._was_on_frame)

        return {"RUNNING_MODAL"}

    def _stage_rendering(self, context: Context):
        self._render_props.render_stage_description = "Rendering"

        frames_recorded = self._api_client.get_frames_recorded()
        if frames_recorded is None:
            self.remove_timer(context)
            self.report({"ERROR"}, "failed to receive recorded frames count")
            return {"CANCELLED"}

        self._render_props.render_stage_progress = frames_recorded / self._frame_count

        if frames_recorded < self._frame_count:
            return {"RUNNING_MODAL"}

        bpy.ops.ow_recorder.load_camera_background()

        self.remove_timer(context)
        self.report({"INFO"}, "Outer Wilds render finished")
        return {"FINISHED"}

    def remove_timer(self, context: Context):
        context.window_manager.event_timer_remove(self._timer)
        self._render_props.is_rendering = False

    def _get_transform_local_to(self, parent: Object, child: Object) -> TransformModel:
        local_matrix = parent.matrix_world.inverted() @ child.matrix_world
        return TransformModel.from_matrix(local_matrix)
