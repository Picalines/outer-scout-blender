from typing import TypedDict

from .transform import TransformJson


class PostSceneJson(TypedDict):
    origin: TransformJson
    hidePlayerModel: bool

