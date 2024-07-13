from bpy.props import EnumProperty
from bpy.types import Operator

from ..bpy_register import bpy_register
from ..properties import SceneProperties


@bpy_register
class ToggleGroundBodyOperator(Operator):
    """Sets the ground body viewport visibility"""

    bl_idname = "outer_scout.set_ground_body_visibility"
    bl_label = "Toggle Ground Body"

    action: EnumProperty(
        name="Action", default="TOGGLE", items=[("TOGGLE", "Toggle", ""), ("SHOW", "Show", ""), ("HIDE", "Hide", "")]
    )

    @classmethod
    def poll(cls, context) -> bool:
        return SceneProperties.from_context(context).has_ground_body

    def execute(self, context):
        scene_props = SceneProperties.from_context(context)
        ground_body = scene_props.ground_body

        match self.action:
            case "TOGGLE":
                hide = not ground_body.hide_get()
            case "SHOW":
                hide = False
            case "HIDE":
                hide = True

        ground_body.hide_set(state=hide)
        for child in ground_body.children:
            child.hide_set(state=hide)

        return {"FINISHED"}
