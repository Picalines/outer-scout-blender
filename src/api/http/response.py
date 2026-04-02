import json
from dataclasses import dataclass
from http import HTTPStatus
from typing import TypeVar

from ...utils import Result

T = TypeVar("T")

HTTP_SUCCESS_RANGE = range(200, 300)

NOT_JSON_ERROR = ValueError("http response is not json")


@dataclass(frozen=True)
class Response:
    status: HTTPStatus
    content_type: str
    body: str

    @property
    def is_success(self) -> bool:
        return self.status in HTTP_SUCCESS_RANGE

    @property
    def is_error(self) -> bool:
        return not self.is_success

    @property
    def is_json(self) -> bool:
        return "json" in self.content_type

    def json(self, _: type[T] = object) -> Result[T, Exception]:
        if not self.is_json:
            return Result.error(NOT_JSON_ERROR)
        try:
            return Result.ok(json.loads(self.body))
        except Exception as e:
            return Result.error(e)
