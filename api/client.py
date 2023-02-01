from typing import Literal

from ..preferences import OWRecorderPreferences
from .models import TransformModel, CameraInfo
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
        return response.body if response.is_success() else None

    def generate_current_ground_body_mesh_list(self, output_file_path: str) -> bool:
        response = self._get_response(Request(
            method='POST',
            url='ground_body/mesh_list',
            query_params={'output_file_path': output_file_path}
        ))
        return response.is_success()

    def get_transform_local_to_ground_body(self, entity: Literal['free_camera', 'player/body', 'player/camera']) -> TransformModel | None:
        response = self._get_response(Request(
            method='GET',
            url=f'{entity}/transform/local_to/ground_body',
        ))
        return TransformModel.from_json_str(response.body) if response.is_success() else None

    def set_transform_local_to_ground_body(self, entity: Literal['free_camera', 'player/body'], new_transform: TransformModel) -> bool:
        response = self._get_response(Request(
            method='PUT',
            url=f'{entity}/transform/local_to/ground_body',
            data=new_transform.to_json(),
        ))
        return response.is_success()

    def get_camera_info(self, camera: Literal['free_camera', 'player/camera']) -> CameraInfo | None:
        response = self._get_response(Request(
            method='GET',
            url=f'{camera}/camera_info',
        ))
        return response.typed_json(CameraInfo) if response.is_success else None

    def set_camera_info(self, camera: Literal['free_camera'], new_info: CameraInfo) -> bool:
        response = self._get_response(Request(
            method='PUT',
            url=f'{camera}/camera_info',
            data=new_info,
        ))
        return response.is_success()

    def _get_response(self, request: Request) -> Response | None:
        return send_request(replace(request, url=self.base_url + request.url)) or Response('', {}, -1)
