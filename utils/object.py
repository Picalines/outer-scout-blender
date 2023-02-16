from typing import Iterable
import re

import bpy
from bpy.types import Object


DUPLICATE_OBJECT_NAME_REGEX = re.compile(r"(.*?)\.\d+")


def set_parent(
    children: Iterable[Object], parent: Object | None, *, keep_transform=True
):
    for child in filter(lambda obj: obj is not None, children):
        child.parent = parent
        if keep_transform and parent is not None:
            child.matrix_parent_inverse = parent.matrix_world.inverted()


def create_empty():
    bpy.ops.object.empty_add()
    return bpy.context.active_object


def get_child_by_path(
    object: Object, path: Iterable[str], mask_duplicates=True
) -> Object | None:
    current = object

    def match_child_name(expected_name: str, actual_name: str):
        matches = actual_name == expected_name

        if not matches and mask_duplicates:
            re_match = re.search(DUPLICATE_OBJECT_NAME_REGEX, actual_name)
            matches = re_match is not None and re_match.group(1) == expected_name

        return matches

    for child_name in path:
        current = next(
            (
                child
                for child in current.children
                if match_child_name(child_name, child.name)
            ),
            None,
        )
        if not current:
            return None

    return current


def iter_parents(object: Object):
    while True:
        object = object.parent
        if object is None:
            break
        yield object
