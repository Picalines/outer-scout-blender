from typing import Any

from bpy.types import Context
from mathutils import Quaternion, Vector

from ..properties import OuterScoutPreferences
from .http import Request, Response
from .models import ApiVersionJson, GroundBodyJson, ObjectJson, ObjectMeshJson, PlayerSectorListJson

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

    def get_api_version(self) -> ApiVersionJson | None:
        response = self._get("api/version", assert_compat=False)
        return response.typed_json(ApiVersionJson) if response.is_ok() else None

    def is_api_supported(self) -> bool:
        if self.api_version is None:
            api_version = self.get_api_version()
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

    def get_object(self, name: str, *, origin: str | None = None) -> ObjectJson | None:
        response = self._get(f"objects/{name}", query={"origin": origin})
        return response.typed_json(ObjectJson) if response.is_ok() else None

    def get_object_mesh(self, name: str) -> ObjectMeshJson | None:
        response = self._get(f"objects/{name}/mesh")
        return response.typed_json(ObjectMeshJson) if response.is_ok() else None

    def get_ground_body(self) -> GroundBodyJson | None:
        response = self._get("player/ground-body")
        return response.typed_json(GroundBodyJson) if response.is_ok() else None

    def get_player_sectors(self) -> PlayerSectorListJson | None:
        response = self._get("player/sectors")
        return response.typed_json(PlayerSectorListJson) if response.is_ok() else None

    def warp_player(self, *, ground_body: str, local_position: Vector, local_rotation: Quaternion) -> bool:
        response = self._post(
            "player/warp",
            data={
                "groundBody": ground_body,
                "transform": {
                    "position": tuple(local_position),
                    "rotation": tuple(local_rotation),
                },
            },
        )

        return response.is_ok()

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
        if response and not response.is_ok():
            self._system_log(f"{response.status} at {method} '{route}': {response.body}")

        return response or Response("", -1)

    def _get(self, route: str, query: dict[str, str] | None = None, *, assert_compat=True) -> Response:
        return self._get_response(route=route, method="GET", query=query, assert_compat=assert_compat)

    def _post(self, route: str, data: Any, query: dict[str, str] | None = None) -> Response:
        return self._get_response(route=route, method="POST", data=data, query=query)

    def _put(self, route: str, data: Any | None = None, query: dict[str, str] | None = None) -> Response:
        return self._get_response(route=route, method="PUT", data=data, query=query)

    def _system_log(self, message: str):
        print(f"outer-scout-blender API: {message}")

