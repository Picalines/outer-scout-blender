import bpy
from bpy.types import Object


GROUND_BODY_COLLECTION_NAME = 'Outer Wilds ground body'


def get_current_ground_body() -> Object | None:
    if GROUND_BODY_COLLECTION_NAME not in bpy.data.collections:
        return None
    ground_body_collection = bpy.data.collections[GROUND_BODY_COLLECTION_NAME]
    return ground_body_collection.objects[0] if any(ground_body_collection.objects) else None
