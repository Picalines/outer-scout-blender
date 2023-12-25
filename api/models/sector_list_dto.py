from typing import TypedDict


class SectorListDTO(TypedDict):
    current: str
    sectors: list[str]

