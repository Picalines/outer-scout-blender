from typing import Literal, NotRequired, TypedDict


class ResolutionJson(TypedDict):
    width: int
    height: int


class PerspectiveJson(TypedDict):
    focalLength: float
    sensorSize: tuple[float, float]
    lensShift: tuple[float, float]
    nearClipPlane: float
    farClipPlane: float


class PerspectiveCameraJson(TypedDict):
    gateFit: Literal["horizontal", "vertical"]
    resolution: ResolutionJson
    perspective: PerspectiveJson


class EquirectCameraJson(TypedDict):
    faceResolution: int


class CameraJson(TypedDict):
    type: Literal["perspective", "equirectangular", "unity"]
    perspective: NotRequired[PerspectiveJson]


class ActiveCameraJson(TypedDict):
    name: str
    camera: CameraJson
