from dataclasses import dataclass, field
from typing import Literal, Any
from urllib.request import Request as UrllibRequest
import urllib
import json


HTTPMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


@dataclass(frozen=True)
class Request:
    url: str
    method: HTTPMethod
    data: Any | None = None
    data_as_json = True
    query_params: dict[str, str] | None = None
    headers: dict[str, str] = field(default_factory=dict)

    def to_urllib_request(self) -> UrllibRequest:
        url = self.url

        if not url.startswith("http"):
            raise ValueError("only http urls are supported")

        method = self.method.upper()
        headers = self.headers
        data = self.data
        query_params = self.query_params
        request_data = None

        headers.setdefault("Accept", "application/json")

        if query_params is not None:
            url += "?" + urllib.parse.urlencode(query_params, doseq=True, safe="/")

        if data is not None:
            if self.data_as_json:
                request_data = json.dumps(data).encode()
                headers["Content-Type"] = "application/json; charset=UTF-8"
            else:
                request_data = urllib.parse.urlencode(data).encode()

        return UrllibRequest(
            url, data=request_data, headers=headers, method=method
        )
