from bpy.props import EnumProperty
from bpy.types import Operator
from mathutils import Matrix

from ..api import (
    APIClient,
    blender_quaternion_to_unity,
    blender_vector_to_unity,
    unity_quaternion_to_blender,
    unity_vector_to_blender,
)
from ..bpy_register import bpy_register
from ..properties import SceneProperties


@bpy_register
class WarpPlayerOperator(Operator):
    """Warp to the Outer Scout scene origin"""

    bl_idname = "ow_recorder.warp"
    bl_label = "Warp"

    destination: EnumProperty(name="Destination", items=[("ORIGIN", "Scene Origin", ""), ("CURSOR", "Cursor", "")])

    def invoke(self, context, _):
        return context.window_manager.invoke_props_dialog(self)

    @classmethod
    def poll(cls, context) -> bool:
        scene_props = SceneProperties.from_context(context)
        is_origin_set = scene_props.has_origin

        if not is_origin_set:
            cls.poll_message_set("Outer Scout scene is not created")

        return is_origin_set

    def execute(self, context):
        scene_props = SceneProperties.from_context(context)
        api_client = APIClient.from_context(context)

        warp_matrix = Matrix.Translation(unity_vector_to_blender(scene_props.origin_position)) @ Matrix.LocRotScale(
            None, unity_quaternion_to_blender(scene_props.origin_rotation), None
        )

        match self.destination:
            case "ORIGIN":
                pass
            case "CURSOR":
                cursor = context.scene.cursor
                cursor_matrix = Matrix(cursor.matrix)
                warp_matrix @= cursor_matrix

        warp_position = blender_vector_to_unity(warp_matrix.to_translation())
        warp_rotation = blender_quaternion_to_unity(warp_matrix.to_quaternion())

        success = api_client.warp_player(
            ground_body=scene_props.origin_parent,
            local_position=warp_position,
            local_rotation=warp_rotation,
        )

        if not success:
            self.report({"ERROR"}, "failed to warp to saved location")
            return {"CANCELLED"}

        return {"FINISHED"}

