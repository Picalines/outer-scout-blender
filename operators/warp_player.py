from bpy.props import EnumProperty
from bpy.types import Operator
from mathutils import Matrix

from ..api import APIClient, Transform
from ..bpy_register import bpy_register
from ..properties import SceneProperties
from ..utils import operator_do


@bpy_register
class WarpPlayerOperator(Operator):
    """Warp to the Outer Scout scene origin"""

    bl_idname = "outer_scout.warp_player"
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

    @operator_do
    def execute(self, context):
        scene_props = SceneProperties.from_context(context)
        api_client = APIClient.from_context(context)

        warp_matrix = Transform.from_matrix(scene_props.origin_matrix).to_right_matrix()

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

                warp_matrix @= cursor_matrix

        api_client.warp_player(
            ground_body=scene_props.origin_parent, local_transform=Transform.from_matrix(warp_matrix).to_left()
        ).then()

