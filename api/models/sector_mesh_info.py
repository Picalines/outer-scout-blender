from typing import TypedDict

from .mesh_info import MeshInfo


class SectorMeshInfo(TypedDict):
    path: str
    plain_meshes: list[MeshInfo]
    streamed_meshes: list[MeshInfo]
