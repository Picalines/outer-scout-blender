from typing import TypedDict

from .transform import TransformJson


class MeshBodyJson(TypedDict):
    name: str
    path: str
    transform: TransformJson


class MeshAssetJson(TypedDict):
    path: str
    transform: TransformJson


class MeshSectorJson(TypedDict):
    path: str
    plainMeshes: list[MeshAssetJson]
    streamedMeshes: list[MeshAssetJson]


class ObjectMeshJson(TypedDict):
    body: MeshBodyJson
    sectors: list[MeshSectorJson]

