from bpy.types import Panel

from ..bpy_register import bpy_register
from ..properties import OWRecorderSceneProperties


@bpy_register
class OW_RECORDER_PT_animatable_props(Panel):
    bl_idname = "OW_RECORDER_PT_animatable_props"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Outer Wilds Recorder"
    bl_label = "Animatable Properties"

    def draw(self, context):
        scene_props = OWRecorderSceneProperties.from_context(context)

        self.layout.prop(scene_props, "time_scale")
