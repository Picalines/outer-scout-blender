import json
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Type, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Response:
    body: str
    status: HTTPStatus

    def is_ok(self) -> bool:
        return self.status in range(200, 300)

    def json(self) -> Any:
        return json.loads(self.body)

    def typed_json(self, model_type: Type[T]) -> T:
        model: model_type = self.json()
        return model

