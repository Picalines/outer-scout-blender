import json
from os import path
from traceback import format_exception

from bpy.types import Object, Operator
from mathutils import Matrix

from ..api import Transform
from ..bpy_register import bpy_register
from ..properties import ObjectProperties
from ..utils import Result, operator_do


@bpy_register
class ImportTransformRecordingOperator(Operator):
    """Import recording file as transform keyframes"""

    bl_idname = "outer_scout.import_transform_recording"
    bl_label = "Import Transform Recording"

    @classmethod
    def poll(cls, context) -> bool:
        active_object: Object = context.active_object
        if not active_object or active_object.type == "CAMERA":
            return False

        return ObjectProperties.of_object(active_object).transform_props.has_recording_path

    @operator_do
    def execute(self, context):
        scene = context.scene
        active_object: Object = context.active_object
        transform_props = ObjectProperties.of_object(active_object).transform_props

        if not path.isfile(transform_props.absolute_recording_path):
            Result.do_error(f'"{transform_props.recording_path}" is not a file')

        with open(transform_props.absolute_recording_path, "r") as recording_file:
            try:
                recording_json = json.load(recording_file)
            except json.JSONDecodeError as json_decode_error:
                Result.do_error(f"invalid json recording file: {json_decode_error}")

        if (anim_data := active_object.animation_data) and (existing_action := anim_data.action):
            for fcurve in list(existing_action.fcurves):
                if fcurve.data_path in ("location", "rotation_quaternion", "scale"):
                    existing_action.fcurves.remove(fcurve)

        active_object.matrix_parent_inverse = Matrix.Identity(4)
        active_object.rotation_mode = "QUATERNION"

        if active_object.parent is not None:
            self.report({"WARNING"}, f'animation of "{active_object.name}" might be broken because it has a parent')

        for frame, transform_json in enumerate(recording_json["values"], start=scene.frame_start):
            try:
                active_object.matrix_world = Transform.from_json(transform_json).to_right_matrix()
            except Exception as exception:
                self.report({"ERROR"}, "".join(format_exception(exception)))
                continue
            active_object.keyframe_insert("location", frame=frame)
            active_object.keyframe_insert("rotation_quaternion", frame=frame)
            active_object.keyframe_insert("scale", frame=frame)
