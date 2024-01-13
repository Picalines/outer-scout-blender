from bpy.types import Operator

from ..api import APIClient
from ..bpy_register import bpy_register
from ..preferences import OWRecorderPreferences


@bpy_register
class OW_RECORDER_OT_check_api_status(Operator):
    """Sends test request to Outer Wilds SceneRecorder API"""

    bl_idname = "ow_recorder.check_api_status"
    bl_label = "Create pivots"

    def execute(self, context):
        api_client = APIClient(OWRecorderPreferences.from_context(context))

        api_status = api_client.get_api_status()

        if not api_status["available"]:
            self.report({"ERROR"}, "SceneRecorder API is not available")
            return {"CANCELLED"}

        self.report({"INFO"}, "SceneRecorder API is available")
        return {"FINISHED"}

