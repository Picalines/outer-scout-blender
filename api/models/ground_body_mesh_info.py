from typing import TypedDict

from .game_object_dto import GameObjectDTO
from .sector_mesh_info import SectorMeshDTO


class GroundBodyMeshDTO(TypedDict):
    body: GameObjectDTO
    sectors: list[SectorMeshDTO]

