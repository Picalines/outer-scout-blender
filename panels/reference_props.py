from bpy.types import Panel

from ..bpy_register import bpy_register
from ..properties import OWRecorderReferencePropertis


@bpy_register
class OW_RECORDER_PT_reference_props(Panel):
    bl_idname = "OW_RECORDER_PT_reference_props"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Outer Wilds Recorder"
    bl_label = "Scene References"

    def draw(self, context):
        reference_props = OWRecorderReferencePropertis.from_context(context)

        self.layout.prop(reference_props, 'ground_body')
        self.layout.prop(reference_props, 'hdri_pivot')
