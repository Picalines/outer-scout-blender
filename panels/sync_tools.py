import bpy


class OWRECORDER_PT_sync_tools(bpy.types.Panel):
    bl_idname = 'OWRECORDER_PT_sync_tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Outer Wilds Recorder'
    bl_label = 'Synchronize'

    def draw(self, context):
        self.layout.label(text='Hello, world!')
