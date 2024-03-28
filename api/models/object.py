from typing import NotRequired, TypedDict

from .transform import TransformJson


class ObjectJson(TypedDict):
    name: str
    transform: NotRequired[TransformJson]

