import bpy
from bpy.types import Object


GROUND_BODY_COLLECTION_NAME = 'Outer Wilds ground body'


HDRI_PIVOT_NAME = 'HDRI pivot'


def get_current_ground_body() -> Object | None:
    if GROUND_BODY_COLLECTION_NAME not in bpy.data.collections:
        return None
    ground_body_collection = bpy.data.collections[GROUND_BODY_COLLECTION_NAME]
    return ground_body_collection.objects[0] if any(ground_body_collection.objects) else None


def get_current_hdri_pivot() -> Object | None:
    return (bpy.data.objects[HDRI_PIVOT_NAME]
            if HDRI_PIVOT_NAME in bpy.data.objects
            else None)


def poll_ow_objects():
    return all((
        get_current_ground_body(),
        get_current_hdri_pivot(),
    ))
