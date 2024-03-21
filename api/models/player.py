from typing import NotRequired, TypedDict


class PlayerSectorJson(TypedDict):
    name: str
    id: NotRequired[str]


class PlayerSectorListJson(TypedDict):
    lastEntered: str
    sectors: list[PlayerSectorJson]

