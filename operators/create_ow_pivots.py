import bpy
from bpy.types import Operator

from ..bpy_register import bpy_register
from ..ow_objects import *


@bpy_register
class OW_RECORDER_OT_create_ow_pivots(Operator):
    '''Creates empties that the addon will use to place objects in Outer Wilds'''

    bl_idname = 'ow_recorder.create_ow_pivots'
    bl_label = 'Create pivots'

    def execute(self, context):
        # pivots collection
        if (pivots_collection := get_pivots_collection()) is None:
            pivots_collection = bpy.data.collections.new(OW_PIVOTS_COLLECTION_NAME)
            context.scene.collection.children.link(pivots_collection)

        # player body pivot
        if (player_body_pivot := get_current_player_body_pivot()) is None:
            player_body_pivot = bpy.data.objects.new(PLAYER_BODY_PIVOT_NAME, None)
            player_body_pivot.empty_display_type = 'PLAIN_AXES'

        if pivots_collection not in player_body_pivot.users_collection:
            pivots_collection.objects.link(player_body_pivot)

        # hdri pivot
        if (hdri_pivot := get_current_hdri_pivot()) is None:
            hdri_pivot = bpy.data.objects.new(HDRI_PIVOT_NAME, None)
            hdri_pivot.empty_display_type = 'PLAIN_AXES'

        if pivots_collection not in hdri_pivot.users_collection:
            pivots_collection.objects.link(hdri_pivot)

        return {'FINISHED'}
