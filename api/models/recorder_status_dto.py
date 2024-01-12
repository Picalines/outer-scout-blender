from typing import TypedDict


class RecorderStatusDTO(TypedDict):
    enabled: bool
    isAbleToRecord: bool
    framesRecorded: int

