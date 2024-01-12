from typing import Any, Generator

from ..preferences import OWRecorderPreferences
from ..utils import GeneratorWithState
from .http import Request, Response
from .models import (
    CameraDTO,
    GameObjectDTO,
    GroundBodyMeshDTO,
    RecorderSettings,
    RecorderStatus,
    RelativeTransformDTO,
    SectorListDTO,
    TransformDTO,
)


class APIClient:
    def __init__(self, preferences: OWRecorderPreferences):
        self.base_url = f"http://localhost:{preferences.api_port}/"

    def get_recorder_status(self) -> RecorderStatus:
        response = self._get("recorder/status")
        return (
            response.typed_json(RecorderStatus)
            if response.is_ok()
            else {"enabled": False, "isAbleToRecord": False, "framesRecorded": 0}
        )

    def get_frames_recorded_async(self) -> Generator[int, None, bool]:
        lines = GeneratorWithState(self._get_async(route="recorder/frames-recorded-async"))

        for line in lines:
            try:
                yield int(line)
            except ValueError:
                pass

        return bool(lines.returned) and lines.returned.is_ok()

    def set_recorder_enabled(self, enabled: bool) -> bool:
        return self._put("recorder/enabled", query={"value": enabled}).is_ok()

    def set_recorder_settings(self, recorder_settings: RecorderSettings) -> bool:
        return self._put("recorder/settings", recorder_settings).is_ok()

    def set_keyframes(self, property: str, from_frame: int, values: list) -> bool:
        return self._put(f"{property}/keyframes", {"fromFrame": from_frame, "values": values}).is_ok()

    def get_ground_body(self) -> GameObjectDTO | None:
        response = self._get("player/ground-body")
        return response.typed_json(GameObjectDTO) if response.is_ok() else None

    def get_player_sectors(self) -> SectorListDTO | None:
        response = self._get("player/sectors")
        return response.typed_json(SectorListDTO) if response.is_ok() else None

    def get_ground_body_meshes(self) -> GroundBodyMeshDTO | None:
        response = self._get("player/ground-body/meshes")
        return response.typed_json(GroundBodyMeshDTO) if response.is_ok() else None

    def get_transform(self, entity: str, *, local_to: str) -> tuple[TransformDTO, TransformDTO] | None:
        response = self._get(f"{entity}/transform", query={"localTo": local_to})
        if not response.is_ok():
            return None

        relative_dto = response.typed_json(RelativeTransformDTO)
        return (TransformDTO.from_json(relative_dto["origin"]), TransformDTO.from_json(relative_dto["transform"]))

    def set_transform(self, entity: str, new_transform: TransformDTO, *, local_to: str) -> bool:
        return self._put(f"{entity}/transform", {"localTo": local_to, "transform": new_transform.to_json()}).is_ok()

    def get_camera_info(self, camera: str) -> CameraDTO | None:
        response = self._get(f"{camera}/camera-info")
        return response.typed_json(CameraDTO) if response.is_ok() else None

    def set_camera_info(self, camera: str, new_info: CameraDTO) -> bool:
        response = self._put(f"{camera}/camera-info", new_info)
        return response.is_ok()

    def warp_to(self, ground_body_name: str, local_transform: TransformDTO) -> bool:
        response = self._post(f"{ground_body_name}/warp", {"localTransform": local_transform.to_json()})
        return response.is_ok()

    def _get_response(
        self, *, route: str, method: str, data: Any | None = None, query: dict[str, str] | None = None
    ) -> Response:
        request = Request(url=self.base_url + route, method=method, data=data, query_params=query)
        response = request.send()
        if response and not response.is_ok():
            self._system_log(f"{response.status} at {method} '{route}': {response.body}")
        return response or Response("", -1)

    def _get(self, route: str, query: dict[str, str] | None = None) -> Response:
        return self._get_response(route=route, method="GET", query=query)

    def _post(self, route: str, data: Any, query: dict[str, str] | None = None) -> Response:
        return self._get_response(route=route, method="POST", data=data, query=query)

    def _put(self, route: str, data: Any | None = None, query: dict[str, str] | None = None) -> Response:
        return self._get_response(route=route, method="PUT", data=data, query=query)

    def _get_response_async(
        self, *, route: str, method: str, data: Any | None = None, query: dict[str, str] | None = None
    ) -> Generator[str, None, Response]:
        request = Request(url=self.base_url + route, method=method, data=data, query_params=query)
        response = yield from request.send_async()
        if response and not response.is_ok():
            self._system_log(f"{response.status} at {method} '{route}': {response.body}")
        return response or Response("", -1)

    def _get_async(self, route: str, query: dict[str, str] | None = None) -> Generator[str, None, Response]:
        return self._get_response_async(route=route, method="GET", query=query)

    def _system_log(self, message: str):
        print(f"outer-wilds-scene-recorder API: {message}")

