from typing import TypedDict


class RecorderSettingsDTO(TypedDict):
    outputDirectory: str
    startFrame: int
    endFrame: int
    frameRate: float
    resolutionX: int
    resolutionY: int
    recordHdri: bool
    recordDepth: bool
    hdriFaceSize: int
    hidePlayerModel: bool
