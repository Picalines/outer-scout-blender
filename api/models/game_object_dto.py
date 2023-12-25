from typing import TypedDict

from .transform import TransformDTO


class GameObjectDTO(TypedDict):
    name: str
    path: str
    transform: TransformDTO
