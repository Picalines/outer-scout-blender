from typing import TypedDict

from .transform import TransformModelJSON
from .sector_mesh_info import SectorMeshInfo


class GroundBodyMeshInfo(TypedDict):
    body_name: str
    body_transform: TransformModelJSON
    sectors: list[SectorMeshInfo]
