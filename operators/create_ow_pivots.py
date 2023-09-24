import bpy
from bpy.types import Operator

from ..bpy_register import bpy_register
from ..properties import OWRecorderReferenceProperties


@bpy_register
class OW_RECORDER_OT_create_ow_pivots(Operator):
    """Creates empties that the addon will use to place objects in Outer Wilds"""

    bl_idname = "ow_recorder.create_ow_pivots"
    bl_label = "Create pivots"

    def execute(self, context):
        reference_props = OWRecorderReferenceProperties.from_context(context)

        if (hdri_pivot := reference_props.hdri_pivot) is None:
            hdri_pivot = bpy.data.objects.new("HDRI Pivot", None)
            hdri_pivot.empty_display_type = "PLAIN_AXES"
            context.scene.collection.objects.link(hdri_pivot)
            reference_props.hdri_pivot = hdri_pivot

        return {"FINISHED"}
