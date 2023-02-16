from typing import TypeVar, Type, TypedDict, Any
from dataclasses import dataclass
from http import HTTPStatus
import json


TTypedDict = TypeVar("TTypedDict", bound=TypedDict)


@dataclass(frozen=True)
class Response:
    body: str
    headers: dict[str, str]
    status: HTTPStatus

    def is_success(self) -> bool:
        return int(self.status) in range(200, 300)

    def json(self) -> Any:
        return json.loads(self.body)

    def typed_json(self, model_type: Type[TTypedDict]) -> TTypedDict:
        model: model_type = self.json()
        return model
