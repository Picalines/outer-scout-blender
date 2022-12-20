from typing import Iterable
import re

import bpy
from bpy.types import Object, Context


DUPLICATE_OBJECT_NAME_REGEX = re.compile(r'(.*?)\.\d+')


def set_parent(context: Context, children: Iterable[Object], parent: Object | None, *, keep_transform = True):
    children = filter(lambda obj: obj is not None, children)

    for child in children:
        child.select_set(state=True)

    context.view_layer.objects.active = parent

    if parent is not None:
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=keep_transform)
    else:
        bpy.ops.object.parent_clear(type='CLEAR' + ('_KEEP_TRANSFORM' if keep_transform else ''))

    for child in children:
        child.select_set(state=False)


def create_empty():
    bpy.ops.object.empty_add()
    return bpy.context.active_object


def get_child_by_path(object: Object, path: Iterable[str], mask_duplicates = True) -> Object | None:
    current = object

    def match_child_name(expected_name: str, actual_name: str):
        matches = actual_name == expected_name

        if not matches and mask_duplicates:
            re_match = re.search(DUPLICATE_OBJECT_NAME_REGEX, actual_name)
            matches = re_match is not None and re_match.group(1) == expected_name

        return matches

    for child_name in path:
        current = next((child for child in current.children if match_child_name(child_name, child.name)), None)
        if not current:
            return None

    return current


def iter_parents(object: Object):
    while True:
        object = object.parent
        if object is None:
            break
        yield object
