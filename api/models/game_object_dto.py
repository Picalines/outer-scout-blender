from typing import TypedDict

from api.models.transform import TransformDTO


class GameObjectDTO(TypedDict):
    name: str
    path: str
    transform: TransformDTO

