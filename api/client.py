from typing import Any, Never

from bpy.types import Context

from ..properties import OuterScoutPreferences
from ..utils import Result
from .http import Request, Response
from .models import (
    ApiVersionJson,
    GenericError,
    GroundBodyJson,
    ObjectJson,
    ObjectMeshJson,
    PlayerSectorListJson,
    PostRecordingJson,
    PostSceneJson,
    RecordingStatusJson,
    Transform,
)

ACCEPTED_API_VERSION = (0, 1)


class APIClient:
    base_url: str
    api_version: tuple[int, int] | None

    def __init__(self, preferences: OuterScoutPreferences):
        self.base_url = f"http://localhost:{preferences.api_port}/"
        self.api_version = None

    @staticmethod
    def from_context(context: Context) -> "APIClient":
        return APIClient(OuterScoutPreferences.from_context(context))

    def get_api_version(self) -> Result[ApiVersionJson, str]:
        return self._get("api/version", assert_compat=False).bind(self._parse_json_response)

    def is_api_supported(self) -> bool:
        if self.api_version is None:
            api_version = self.get_api_version().unwrap_or(None)
            if api_version:
                self.api_version = (api_version["major"], api_version["minor"])

        if self.api_version is None:
            return False

        return self.api_version[0] == ACCEPTED_API_VERSION[0] and self.api_version[1] >= ACCEPTED_API_VERSION[1]

    def assert_compatability(self):
        if not self.is_api_supported():
            raise AssertionError(
                "current Outer Scout version is not supported"
                if self.api_version is not None
                else "failed to connect to the Outer Scout API"
            )

    def post_scene(self, scene: PostSceneJson) -> Result[Never, str]:
        return self._post("scene", data=scene)

    def post_scene_recording(self, recording: PostRecordingJson) -> Result[Never, str]:
        return self._post("scene/recording", data=recording)

    def get_recording_status(self) -> Result[RecordingStatusJson, str]:
        return self._get("scene/recording/status").bind(self._parse_json_response)

    def get_object(self, name: str, *, origin: str | None = None) -> Result[ObjectJson, str]:
        return self._get(f"objects/{name}", query={"origin": origin}).bind(self._parse_json_response)

    def get_object_mesh(self, name: str) -> Result[ObjectMeshJson, str]:
        return self._get(f"objects/{name}/mesh").bind(self._parse_json_response)

    def get_ground_body(self) -> Result[GroundBodyJson, str]:
        return self._get("player/ground-body").bind(self._parse_json_response)

    def get_player_sectors(self) -> Result[PlayerSectorListJson, str]:
        return self._get("player/sectors").bind(self._parse_json_response)

    def warp_player(self, *, ground_body: str, local_transform: Transform) -> Result[Never, str]:
        return self._post(
            "player/warp", data={"groundBody": ground_body, "transform": local_transform.to_json(scale=False)}
        )

    @Result.do(error=str)
    def _get_response(
        self,
        *,
        route: str,
        method: str,
        data: Any | None = None,
        query: dict[str, str] | None = None,
        assert_compat=True,
    ) -> Response:
        if assert_compat:
            self.assert_compatability()

        request = Request(url=self.base_url + route, method=method, data=data, query_params=query)

        response = request.send()

        error_prefix = "Outer Scout API error: "

        if not response.is_success:
            generic_error = response.json(GenericError).map_error(lambda _: error_prefix + response.body).then()
            Result.do_error(error_prefix + generic_error["error"] if "error" in generic_error else response.body)

        return response

    @staticmethod
    def _parse_json_response(response: Response) -> Result[object, str]:
        return response.json().map_error(lambda e: f"API internal json error: {e}")

    def _get(self, route: str, query: dict[str, str] | None = None, *, assert_compat=True):
        return self._get_response(route=route, method="GET", query=query, assert_compat=assert_compat)

    def _post(self, route: str, data: Any, query: dict[str, str] | None = None):
        return self._get_response(route=route, method="POST", data=data, query=query)

    def _put(self, route: str, data: Any | None = None, query: dict[str, str] | None = None):
        return self._get_response(route=route, method="PUT", data=data, query=query)

