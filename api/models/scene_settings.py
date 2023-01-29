from typing import TypedDict


class SceneSettings(TypedDict):
    ground_body_name: str
    frame_count: int
    frame_rate: float
    resolution_x: int
    resolution_y: int
    hdri_face_size: int
    hide_player_model: bool
