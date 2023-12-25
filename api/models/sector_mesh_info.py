from typing import TypedDict

from .mesh_info import MeshDTO


class SectorMeshDTO(TypedDict):
    path: str
    plainMeshes: list[MeshDTO]
    streamedMeshes: list[MeshDTO]
