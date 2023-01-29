from ..preferences import OWRecorderPreferences
from .http import send_request, Request, Response

from dataclasses import replace


class APIClient:
    def __init__(self, preferences: OWRecorderPreferences):
        self.base_url = f'http://localhost:{preferences.api_port}/'

    def get_ground_body_name(self) -> str | None:
        response = self._get_response(Request(
            url='ground_body/name',
            method='GET'
        ))
        return response.body if response.is_success() else None

    def _get_response(self, request: Request) -> Response:
        return send_request(replace(request, url=self.base_url + request.url))
