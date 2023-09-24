from typing import TypedDict


class RecorderSettings(TypedDict):
    output_directory: str
    start_frame: int
    end_frame: int
    frame_rate: float
    resolution_x: int
    resolution_y: int
    record_hdri: bool
    record_depth: bool
    hdri_face_size: int
    hide_player_model: bool
    show_progress_gui: bool
