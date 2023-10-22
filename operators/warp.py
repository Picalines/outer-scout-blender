from bpy.types import Context, Operator

from ..bpy_register import bpy_register
from ..properties import OWRecorderSceneProperties
from ..preferences import OWRecorderPreferences
from ..api import APIClient, TransformModel


@bpy_register
class OW_RECORDER_OT_warp(Operator):
    """Warp to previously saved location"""

    bl_idname = "ow_recorder.warp"
    bl_label = "Warp"

    @classmethod
    def poll(cls, context) -> bool:
        scene_props = OWRecorderSceneProperties.from_context(context)
        return scene_props.has_saved_warp

    def invoke(self, context: Context, _):
        api_client = APIClient(OWRecorderPreferences.from_context(context))
        scene_props = OWRecorderSceneProperties.from_context(context)

        success = api_client.warp_to(
            scene_props.warp_ground_body, TransformModel.from_components_tuple(scene_props.warp_transform)
        )

        if not success:
            self.report({"ERROR"}, "failed to warp to saved location")
            return {"CANCELLED"}

        return {"FINISHED"}
