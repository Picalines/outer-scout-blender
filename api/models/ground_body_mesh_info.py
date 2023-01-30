from typing import TypedDict

from .transform import TransformModelJSON
from .mesh_info import MeshInfo


class GroundBodyMeshInfo(TypedDict):
    body_name: str
    body_transform: TransformModelJSON
    plain_meshes: list[MeshInfo]
    streamed_meshes: list[MeshInfo]
