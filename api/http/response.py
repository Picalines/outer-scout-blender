from typing import TypeVar, Type, TypedDict
from dataclasses import dataclass
from http import HTTPStatus
import json


TTypedDict = TypeVar('TTypedDict', bound=TypedDict)


@dataclass(frozen=True)
class Response:
    body: str
    headers: dict[str, str]
    status: HTTPStatus

    def is_success(self) -> bool:
        return int(self.status) in range(200, 300)

    def typed_json(self, model_type: Type[TTypedDict]) -> TTypedDict:
        model: model_type = json.loads(self.body)
        return model
