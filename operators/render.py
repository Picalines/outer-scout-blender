from bpy.types import Operator, Context, Event, Object
from bpy.props import BoolProperty, IntProperty
from bpy.path import abspath as bpy_abspath

from ..preferences import OWRecorderPreferences
from ..api.models import RecorderSettings, TransformModel
from ..api import APIClient
from ..operators.load_ground_body import get_current_ground_body


class OW_RECORDER_OT_render(Operator):
    '''Render footage in Outer Wilds and import it to current project'''

    bl_idname = 'ow_recorder.render'
    bl_label = 'Render'

    _timer = None
    _api_client: APIClient = None
    _frame_count: int = 0

    hide_player_model: BoolProperty(
        name='Hide player model',
        default=True,
    )

    hdri_face_size: IntProperty(
        name='HDRI face size',
        default=512,
        min=10,
    )

    @classmethod
    def poll(cls, _) -> bool:
        return get_current_ground_body() is not None

    def invoke(self, context: Context, _):
        self._api_client = APIClient(OWRecorderPreferences.from_context(context))

        if self._api_client.get_is_recording():
            self.report({'ERROR'}, 'already recording')
            return {'CANCELLED'}

        self._frame_count = context.scene.frame_end - context.scene.frame_start

        recorder_settings: RecorderSettings = {
            'output_directory': bpy_abspath('//Outer Wilds/footage/'),
            'frame_count': self._frame_count,
            'frame_rate': context.scene.render.fps,
            'resolution_x': context.scene.render.resolution_x,
            'resolution_y': context.scene.render.resolution_y,
            'hdri_face_size': self.hdri_face_size,
            'hide_player_model': self.hide_player_model,
        }

        if not self._api_client.set_recorder_settings(recorder_settings):
            self.report({'ERROR'}, 'failed to set recorder settings')
            return {'CANCELLED'}

        if not self._api_client.get_is_able_to_record():
            self.report({'ERROR'}, 'unable to record')
            return {'CANCELLED'}

        self._send_animation_data(context)

        if not self._api_client.set_is_recording(True):
            self.report({'ERROR'}, 'failed to start recording')
            return {'CANCELLED'}

        self._timer = context.window_manager.event_timer_add(1, window=context.window)
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def _send_animation_data(self, context: Context):
        frame_start = context.scene.frame_start

        was_on_frame = context.scene.frame_current

        for frame_offset in range(self._frame_count):
            context.scene.frame_set(frame=frame_start + frame_offset)

            ground_body = get_current_ground_body()
            camera = context.scene.camera
            new_free_camera_transform = self._get_transform_local_to(ground_body, camera)\
                .blender_to_unity()\
                .to_json()

            # TODO: hdri_pivot & player
            success = self._api_client.set_animation_value_at_frame(
                'free_camera/transform', frame_offset, new_free_camera_transform)

            if not success:
                self.report({'WARNING'}, f'failed to send animation data at frame {context.scene.frame_current}')

        context.scene.frame_set(frame=was_on_frame)

    def modal(self, context: Context, event: Event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        frames_recorded = self._api_client.get_frames_recorded()
        if frames_recorded is None:
            self.remove_timer(context)
            self.report({'ERROR'}, 'failed to receive recorded frames count')
            return {'CANCELLED'}

        if frames_recorded < self._frame_count:
            return {'PASS_THROUGH'}

        self.remove_timer(context)
        return {'FINISHED'}

    def remove_timer(self, context: Context):
        context.window_manager.event_timer_remove(self._timer)

    def _get_transform_local_to(self, parent: Object, child: Object) -> TransformModel:
        local_matrix = parent.matrix_world.inverted() @ child.matrix_world
        return TransformModel.from_matrix(local_matrix)
