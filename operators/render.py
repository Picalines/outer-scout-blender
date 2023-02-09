from typing import Literal

import bpy
from bpy.types import Operator, Context, Event, Object
from bpy.path import abspath as bpy_abspath

from ..bpy_register import bpy_register
from ..preferences import OWRecorderPreferences
from ..properties import OWRecorderRenderProperties
from ..api.models import RecorderSettings, TransformModel, TransformModelJSON
from ..api import APIClient
from ..operators.load_ground_body import get_current_ground_body


@bpy_register
class OW_RECORDER_OT_render(Operator):
    '''Render footage in Outer Wilds and import it to current project'''

    bl_idname = 'ow_recorder.render'
    bl_label = 'Render'

    _timer = None
    _api_client: APIClient = None
    _was_on_frame: int = 0
    _frame_count: int = 0
    _frame_offset: int = 0
    _render_props: OWRecorderRenderProperties = None
    _stage: Literal['SENDING_ANIMATION', 'RENDERING'] = ''

    @classmethod
    def poll(cls, _) -> bool:
        return get_current_ground_body() is not None

    def invoke(self, context: Context, _):
        self._api_client = APIClient(OWRecorderPreferences.from_context(context))

        if self._api_client.get_is_recording():
            self.report({'ERROR'}, 'already recording')
            return {'CANCELLED'}

        self._was_on_frame = context.scene.frame_current

        self._render_props = OWRecorderRenderProperties.from_context(context)

        self._frame_count = context.scene.frame_end - context.scene.frame_start + 1 + self._render_props.render_end_margin

        recorder_settings: RecorderSettings = {
            'output_directory': bpy_abspath('//Outer Wilds/footage/'),
            'frame_count': self._frame_count,
            'frame_rate': context.scene.render.fps,
            'resolution_x': context.scene.render.resolution_x,
            'resolution_y': context.scene.render.resolution_y,
            'hdri_face_size': self._render_props.hdri_face_size,
            'hide_player_model': self._render_props.hide_player_model,
        }

        if not self._api_client.set_recorder_settings(recorder_settings):
            self.report({'ERROR'}, 'failed to set recorder settings')
            return {'CANCELLED'}

        if not self._api_client.get_is_able_to_record():
            self.report({'ERROR'}, 'unable to record')
            return {'CANCELLED'}

        self._timer = context.window_manager.event_timer_add(self._render_props.render_timer_delay, window=context.window)
        context.window_manager.modal_handler_add(self)

        self._frame_offset = 0
        self._stage = 'SENDING_ANIMATION'

        self._render_props.is_rendering = True

        return {'RUNNING_MODAL'}

    def modal(self, context: Context, event: Event):
        if event.type != 'TIMER':
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        if self._stage == 'SENDING_ANIMATION':
            return self._stage_sending_animation(context)
        elif self._stage == 'RENDERING':
            return self._stage_rendering(context)
        else:
            raise NotImplemented

    def _stage_sending_animation(self, context: Context):
        self._render_props.render_stage_description = 'Sending animation'
        self._render_props.render_stage_progress = self._frame_offset / self._frame_count

        frame_start = context.scene.frame_start
        ground_body = get_current_ground_body()
        camera = context.scene.camera

        # TODO: hdri_pivot & player
        animation_transforms: dict[str, list[TransformModelJSON]] = {
            'free_camera/transform': [],
        }

        chunk_start_frame = self._frame_offset

        for _ in range(self._render_props.animation_chunk_size):
            context.scene.frame_set(frame=frame_start + self._frame_offset)

            animation_transforms['free_camera/transform'].append(self._get_transform_local_to(ground_body, camera)
                .blender_to_unity()
                .to_json())

            self._frame_offset += 1
            if self._frame_offset >= self._frame_count:
                break

        for animation_name, transforms in animation_transforms.items():
            success = self._api_client.set_animation_values_from_frame(animation_name, chunk_start_frame, transforms)

            if not success:
                self.report({'WARNING'}, f'failed to send animation data at frame {chunk_start_frame}')

        if self._frame_offset >= self._frame_count:
            if not self._api_client.set_is_recording(True):
                self.report({'ERROR'}, 'failed to start recording')
                return {'CANCELLED'}

            self._stage = 'RENDERING'
            context.scene.frame_set(frame=self._was_on_frame)

        return {'RUNNING_MODAL'}

    def _stage_rendering(self, context: Context):
        self._render_props.render_stage_description = 'Rendering'

        frames_recorded = self._api_client.get_frames_recorded()
        if frames_recorded is None:
            self.remove_timer(context)
            self.report({'ERROR'}, 'failed to receive recorded frames count')
            return {'CANCELLED'}

        self._render_props.render_stage_progress = frames_recorded / self._frame_count

        if frames_recorded < self._frame_count:
            return {'RUNNING_MODAL'}

        bpy.ops.ow_recorder.load_camera_background()

        self.remove_timer(context)
        self.report({'INFO'}, 'Outer Wilds render finished')
        return {'FINISHED'}

    def remove_timer(self, context: Context):
        context.window_manager.event_timer_remove(self._timer)
        self._render_props.is_rendering = False

    def _get_transform_local_to(self, parent: Object, child: Object) -> TransformModel:
        local_matrix = parent.matrix_world.inverted() @ child.matrix_world
        return TransformModel.from_matrix(local_matrix)
