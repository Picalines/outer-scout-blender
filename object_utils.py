from typing import Iterable

import bpy
from bpy.types import Object, Context


def set_parent(context: Context, children: Iterable[Object], parent: Object, *, keep_transform = True):
    children = filter(lambda obj: obj is not None, children)

    for child in children:
        child.select_set(state=True)

    context.view_layer.objects.active = parent

    bpy.ops.object.parent_set(type='OBJECT', keep_transform=keep_transform)

    for child in children:
        child.select_set(state=False)


def create_empty():
    bpy.ops.object.empty_add()
    return bpy.context.active_object
