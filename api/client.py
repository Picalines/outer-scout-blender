from ..preferences import OWRecorderPreferences
from .http import send_request, Request, Response

from dataclasses import replace


class APIClient:
    def __init__(self, preferences: OWRecorderPreferences):
        self.base_url = f'http://localhost:{preferences.api_port}/'

    def get_ground_body_name(self) -> str | None:
        response = self._get_response(Request(
            method='GET',
            url='ground_body/name',
        ))
        return response.body if response is not None and response.is_success() else None

    def generate_current_ground_body_mesh_list(self, output_file_path: str) -> bool:
        response = self._get_response(Request(
            method='POST',
            url='ground_body/mesh_list',
            query_params={'output_file_path': output_file_path}
        ))
        return response is not None and response.is_success()

    def _get_response(self, request: Request) -> Response | None:
        return send_request(replace(request, url=self.base_url + request.url))
