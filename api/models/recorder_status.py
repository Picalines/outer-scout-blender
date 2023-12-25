from typing import TypedDict


class RecorderStatus(TypedDict):
    enabled: bool
    isAbleToRecord: bool
    framesRecorded: int

