from typing import TypedDict

from .transform import TransformJson


class ObjectJson(TypedDict):
    name: str
    transform: TransformJson
