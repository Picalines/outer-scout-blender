from math import radians

from bpy.props import EnumProperty
from bpy.types import Operator
from mathutils import Matrix, Quaternion, Vector

from ..api import APIClient, blender_matrix_to_unity, unity_matrix_to_blender
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

        warp_matrix = unity_matrix_to_blender(
            Matrix.LocRotScale(Vector(scene_props.origin_position), Quaternion(scene_props.origin_rotation), None)
        )

        match self.destination:
            case "ORIGIN":
                pass
            case "CURSOR":
                cursor = context.scene.cursor
                cursor_matrix = Matrix(cursor.matrix)

                tool = context.workspace.tools.from_space_view3d_mode("OBJECT")
                cursor3d_props = tool.operator_properties("view3d.cursor3d")

                if cursor3d_props.use_depth and cursor3d_props.orientation == "GEOM":
                    cursor_matrix @= Matrix.Translation((0, 0, 1.5))

                warp_matrix @= (
                    Matrix.Rotation(radians(-90), 4, (1, 0, 0))
                    @ cursor_matrix
                    @ Matrix.Rotation(radians(90), 4, (1, 0, 0))
                )

        warp_matrix = blender_matrix_to_unity(warp_matrix)
        warp_position = warp_matrix.to_translation()
        warp_rotation = warp_matrix.to_quaternion()
        (w, x, y, z) = warp_rotation
        warp_rotation = (x, y, z, w)

        success = api_client.warp_player(
            ground_body=scene_props.origin_parent,
            local_position=warp_position,
            local_rotation=warp_rotation,
        )

        if not success:
            self.report({"ERROR"}, "failed to warp to saved location")
            return {"CANCELLED"}

        return {"FINISHED"}

