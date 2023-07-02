import bpy.types


def get_id_type(id: bpy.types.ID) -> str:
    if isinstance(id, bpy.types.LightProbe):
        id_type = "LIGHT_PROBE"
    else:
        id_type = id.bl_rna.identifier.upper()
    return id_type
