import bpy
from bpy.types import Object, Collection


GROUND_BODY_COLLECTION_NAME = 'Outer Wilds ground body'


OW_PIVOTS_COLLECTION_NAME = 'Outer Wilds Pivots'
PLAYER_BODY_PIVOT_NAME = 'Player body pivot'
HDRI_PIVOT_NAME = 'HDRI pivot'


def get_current_ground_body() -> Object | None:
    if GROUND_BODY_COLLECTION_NAME not in bpy.data.collections:
        return None
    ground_body_collection = bpy.data.collections[GROUND_BODY_COLLECTION_NAME]
    return ground_body_collection.objects[0] if any(ground_body_collection.objects) else None


def get_pivots_collection() -> Collection | None:
    if OW_PIVOTS_COLLECTION_NAME not in bpy.data.collections:
        return None
    return bpy.data.collections[OW_PIVOTS_COLLECTION_NAME]


def get_current_player_body_pivot() -> Object | None:
    if (pivots_collection := get_pivots_collection()) is None:
        return None
    return next((object for object in pivots_collection.objects if object.name.startswith(PLAYER_BODY_PIVOT_NAME)), None)


def get_current_hdri_pivot() -> Object | None:
    if (pivots_collection := get_pivots_collection()) is None:
        return None
    return next((object for object in pivots_collection.objects if object.name.startswith(HDRI_PIVOT_NAME)), None)


def poll_ow_objects():
    return all((
        get_current_ground_body(),
        get_current_player_body_pivot(),
        get_current_hdri_pivot(),
    ))
