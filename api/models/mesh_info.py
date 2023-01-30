from typing import TypedDict
from .transform import TransformModelJSON


class MeshInfo(TypedDict):
    path: str
    transform: TransformModelJSON
