from typing import TypedDict


class PostRecordingJson(TypedDict):
    frameRate: int
    startFrame: int
    endFrame: int


class RecordingStatusJson(TypedDict):
    inProgress: bool
    startFrame: int
    endFrame: int
    currentFrame: int
    framesRecorded: int
