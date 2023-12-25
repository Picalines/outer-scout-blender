import json
import urllib
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any, Generator, Literal
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
                    body=http_response.read().decode(http_response.headers.get_content_charset("utf-8")),
                )

        except urllib.error.HTTPError as http_error:
            return Response(
                status=HTTPStatus(http_error.code),
                body=str(http_error.reason),
            )

        except OSError as os_error:
            print(os_error)

        return None

    def send_async(self, *, join_body=False) -> Generator[str, None, Response | None]:
        http_request = self._to_urllib_request()

        try:
            lines = []

            with urllib.request.urlopen(http_request) as http_response:
                charset = http_response.headers.get_content_charset("utf-8")
                for line in http_response:
                    decoded_line = line.decode(charset)
                    yield decoded_line

                    if join_body:
                        lines.append(decoded_line)

            return Response(status=http_response.status, body="\n".join(lines))

        except urllib.error.HTTPError as http_error:
            return Response(status=http_error.code, body=str(http_error.reason))

        except OSError as os_error:
            print(os_error)

        return None

    def _to_urllib_request(self) -> UrllibRequest:
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

        return UrllibRequest(url, data=request_data, headers=headers, method=method)
