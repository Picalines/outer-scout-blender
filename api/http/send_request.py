from .request import Request
from .response import Response

from http import HTTPStatus
import urllib.parse
import urllib.error
import urllib.request
import json


def send_request(request: Request) -> Response | None:
    url = request.url

    if not url.startswith('http'):
        raise ValueError('only http urls are supported')

    method = request.method.upper()
    headers = request.headers
    data = request.data
    query_params = request.query_params
    request_data = None

    headers.setdefault('Accept', 'application/json')

    if query_params is not None:
        url += '?' + urllib.parse.urlencode(query_params, doseq=True, safe='/')

    if data is not None:
        if request.data_as_json:
            request_data = json.dumps(data).encode()
            headers['Content-Type'] = 'application/json; charset=UTF-8'
        else:
            request_data = urllib.parse.urlencode(data).encode()

    http_request = urllib.request.Request(
        url, data=request_data, headers=headers, method=method
    )

    try:
        http_response = urllib.request.urlopen(http_request)
        response = Response(
            body=http_response.read().decode(
                http_response.headers.get_content_charset('utf-8')
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
