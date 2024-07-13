from typing import TypedDict


class KeyframeJson(TypedDict):
    value: float


class PropertyAnimationJson(TypedDict):
    keyframes: dict[int, KeyframeJson]


class PutKeyframesJson(TypedDict):
    properties: dict[str, PropertyAnimationJson]
