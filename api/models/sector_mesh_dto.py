from typing import TypedDict

from .mesh_dto import MeshDTO


class SectorMeshDTO(TypedDict):
    path: str
    plainMeshes: list[MeshDTO]
    streamedMeshes: list[MeshDTO]
