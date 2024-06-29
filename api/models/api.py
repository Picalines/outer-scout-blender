from typing import TypedDict, NotRequired


class ApiVersionJson(TypedDict):
    patch: int
    minor: int
    major: int


class ProblemJson(TypedDict):
    type: str
    title: NotRequired[str]
    detail: NotRequired[str]
