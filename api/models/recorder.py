from typing import Literal, TypedDict


class ColorTextureRecorderJson(TypedDict):
    property: Literal["camera.renderTexture.color", "camera.renderTexture.depth"]
    outputPath: str
    format: Literal["mp4"]
    constantRateFactor: int


class TransformRecorderJson(TypedDict):
    outputPath: str
    format: Literal["json"]

