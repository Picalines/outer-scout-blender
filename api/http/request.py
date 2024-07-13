import json
import urllib
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any, Literal
from urllib.parse import quote as url_encode
from urllib.request import Request as UrllibRequest

from .response import Response

HTTPMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


@dataclass(frozen=True)
class Request:
    url: str
    method: HTTPMethod
    data: Any | None = None
    data_as_json = True
    query_params: dict[str, str] | None = None
    headers: dict[str, str] = field(default_factory=dict)

    def send(self) -> Response | None:
        http_request = self._to_urllib_request()

        try:
            with urllib.request.urlopen(http_request) as http_response:
                return Response(
                    status=http_response.status,
                    content_type=http_response.headers.get_content_type(),
                    body=http_response.read().decode(http_response.headers.get_content_charset("utf-8")),
                )
        except urllib.error.HTTPError as http_error:
            return Response(
                status=HTTPStatus(http_error.code),
                content_type=http_error.headers.get_content_type(),
                body=http_error.read().decode(http_error.headers.get_content_charset("utf-8")),
            )
        except OSError as os_error:
            print(os_error)

        return None

    def _to_urllib_request(self) -> UrllibRequest:
        url = url_encode(self.url, safe="/:")

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

        return UrllibRequest(url, data=request_data, headers=headers, method=method)
