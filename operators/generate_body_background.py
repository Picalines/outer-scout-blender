from pathlib import Path

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from ..bpy_register import bpy_register
from ..properties import OuterScoutPreferences


@bpy_register
class GenerateBodyBackgroundOperator(Operator):
    """Call outer_scout.generate_body in background environment"""

    bl_idname = "outer_scout.generate_body_background"
    bl_label = "Generate body (background)"

    body_name: StringProperty(name="Ground Body")

    def execute(self, context):
        preferences = OuterScoutPreferences.from_context(context)

        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()
        for c in context.scene.collection.children:
            context.scene.collection.children.unlink(c)

        try:
            result = bpy.ops.outer_scout.generate_body(body_name=self.body_name)
        except RuntimeError:
            result = {"ERROR"}

        if result != {"FINISHED"}:
            input("Press enter to exit...")
            return {"CANCELLED"}

        context.view_layer.update()

        bpy.ops.wm.save_as_mainfile(
            filepath=str(Path(preferences.ow_bodies_folder).joinpath(self.body_name + ".blend"))
        )

        bpy.ops.wm.quit_blender()
        return {"FINISHED"}
