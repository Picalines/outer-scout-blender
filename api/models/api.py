from typing import TypedDict


class ApiVersionJson(TypedDict):
    patch: int
    minor: int
    major: int


class GenericError(TypedDict):
    error: str

