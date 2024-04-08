from bpy.path import abspath
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import PropertyGroup

from ..bpy_register import bpy_register


@bpy_register
class TransformRecordingProperties(PropertyGroup):
    recording_path: StringProperty(
        name="Transform Recording Path",
        description="The path to the file where the transform recording (json) will be saved",
        subtype="FILE_PATH",
        default="",
        options=set(),
    )

    mode: EnumProperty(
        name="Transform Mode",
        default="RECORD",
        items=[
            ("RECORD", "Record", "Record Unity object transform and import it as keyframes of this object"),
            ("APPLY", "Replay", "Send this object's transform keyframes to Outer Wilds"),
        ],
        options=set(),
    )

    record_once: BoolProperty(
        name="Record Once",
        description="After the first recording, the addon will automatically set the 'Replay' mode",
        default=True,
        options=set(),
    )

    @property
    def has_recording_path(self):
        return self.recording_path != ""

    @property
    def absolute_recording_path(self) -> str:
        return abspath(self.recording_path)

