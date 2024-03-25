import json
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Type, TypeVar

from ..models import GenericError

T = TypeVar("T")

HTTP_SUCCESS_RANGE = range(200, 300)


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

    def generic_error(self) -> GenericError | None:
        if self.is_success:
            return None

        if not self.is_json:
            return {"error": self.body}

        try:
            return self.typed_json(GenericError)
        except:
            return {"error": self.body}

    def json(self) -> Any:
        if self.content_type != "application/json":
            raise ValueError("http response is not json")
        return json.loads(self.body)

    def typed_json(self, model_type: Type[T]) -> T:
        model: model_type = self.json()
        return model

