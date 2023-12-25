from bpy.types import Context, Operator

from ..api import APIClient
from ..bpy_register import bpy_register
from ..preferences import OWRecorderPreferences
from ..properties import OWRecorderReferenceProperties, OWRecorderSceneProperties


@bpy_register
class OW_RECORDER_OT_save_warp_transform(Operator):
    """Save new warp position"""

    bl_idname = "ow_recorder.save_warp_transform"
    bl_label = "Save warp location"

    @classmethod
    def poll(cls, context) -> bool:
        reference_props = OWRecorderReferenceProperties.from_context(context)
        return reference_props.ground_body is not None

    def invoke(self, context: Context, _):
        api_client = APIClient(OWRecorderPreferences.from_context(context))

        ground_body = api_client.get_ground_body()
        if ground_body is None:
            self.report({"ERROR"}, "failed to get current ground body")
            return {"CANCELLED"}

        transforms = api_client.get_transform("player/body", local_to=ground_body["name"])
        if transforms is None:
            self.report({"ERROR"}, "failed to receive player transform")
            return {"CANCELLED"}

        _, player_transform = transforms

        scene_props = OWRecorderSceneProperties.from_context(context)
        scene_props.warp_ground_body = ground_body["name"]
        scene_props.warp_transform = player_transform.components()
        scene_props.has_saved_warp = True

        return {"FINISHED"}

