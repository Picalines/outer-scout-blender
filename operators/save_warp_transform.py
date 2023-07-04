from bpy.types import Context, Operator

from ..bpy_register import bpy_register
from ..properties import OWRecorderSceneProperties, OWRecorderReferencePropertis
from ..preferences import OWRecorderPreferences
from ..api import APIClient


@bpy_register
class OW_RECORDER_OT_save_warp_transform(Operator):
    """Save new warp position"""

    bl_idname = "ow_recorder.save_warp_transform"
    bl_label = "Save warp location"

    @classmethod
    def poll(cls, context) -> bool:
        reference_props = OWRecorderReferencePropertis.from_context(context)
        return reference_props.ground_body is not None

    def invoke(self, context: Context, _):
        api_client = APIClient(OWRecorderPreferences.from_context(context))

        player_transform = api_client.get_transform_local_to_ground_body("player_body")
        if player_transform is None:
            self.report({"ERROR"}, "failed to receive player transform")
            return {"CANCELLED"}
        
        ground_body_name = api_client.get_ground_body_name()
        if ground_body_name is None:
            self.report({"ERROR"}, "failed to get current ground body name")
            return {"CANCELLED"}

        scene_props = OWRecorderSceneProperties.from_context(context)
        scene_props.warp_ground_body = ground_body_name
        scene_props.warp_transform = player_transform.to_components_tuple()
        scene_props.has_saved_warp = True

        return {"FINISHED"}
