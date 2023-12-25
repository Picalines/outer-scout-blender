from typing import TypedDict

from .transform import TransformDTOJson


class MeshDTO(TypedDict):
    path: str
    globalTransform: TransformDTOJson
    localTransform: TransformDTOJson

