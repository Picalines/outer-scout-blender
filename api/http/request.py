from dataclasses import dataclass, field
from typing import Literal, Any


HTTPMethod = Literal['GET', 'POST', 'PATCH', 'DELETE']


@dataclass(frozen=True)
class Request:
    url: str
    method: HTTPMethod
    data: Any | None = None
    data_as_json = True
    query_params: dict[str, str] | None = None
    headers: dict[str, str] = field(default_factory=dict)
