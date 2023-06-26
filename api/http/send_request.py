from .request import Request
from .response import Response

from http import HTTPStatus
from typing import Generator
import urllib.parse
import urllib.error
import urllib.request


def send_request(request: Request) -> Response | None:
    http_request = request.to_urllib_request()

    try:
        with urllib.request.urlopen(http_request) as http_response:
            response = Response(
                body=http_response.read().decode(
                    http_response.headers.get_content_charset("utf-8")
                ),
                headers=http_response.headers,
                status=http_response.status,
            )
    except urllib.error.HTTPError as http_error:
        response = Response(
            body=str(http_error.reason),
            headers=dict(http_error.headers),
            status=HTTPStatus(http_error.code),
        )
    except OSError:
        response = None

    return response


def send_request_async_lines(request: Request) -> Generator[str, None, HTTPStatus | urllib.error.HTTPError | OSError]:
    http_request = request.to_urllib_request()

    try:
        with urllib.request.urlopen(http_request) as http_response:
            charset = http_response.headers.get_content_charset("utf-8")
            for line in http_response:
                yield line.decode(charset)

        return http_response.status
    except urllib.error.HTTPError or OSError as error:
        return error
