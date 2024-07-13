from typing import TypedDict

from .transform import TransformJson


class GroundBodyJson(TypedDict):
    name: str
    transform: TransformJson
