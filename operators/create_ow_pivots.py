import bpy
from bpy.types import Operator

from ..bpy_register import bpy_register
from ..ow_objects import get_current_hdri_pivot, HDRI_PIVOT_NAME


@bpy_register
class OW_RECORDER_OT_create_ow_pivots(Operator):
    '''Creates empties that the addon will use to place objects in Outer Wilds'''

    bl_idname = 'ow_recorder.create_ow_pivots'
    bl_label = 'Create pivots'

    def execute(self, context):
        if (hdri_pivot := get_current_hdri_pivot()) is None:
            hdri_pivot = bpy.data.objects.new(HDRI_PIVOT_NAME, None)
            hdri_pivot.empty_display_type = 'PLAIN_AXES'
            context.scene.collection.objects.link(hdri_pivot)

        return {'FINISHED'}
