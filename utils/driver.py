from bpy.types import ID, bpy_struct


def add_single_prop_driver(
    struct: bpy_struct,
    data_path: str,
    *,
    target_id: ID,
    target_data_path: str,
    array_index=-1,
    var_name="v",
    expression: str | None = None,
):
    driver = struct.driver_add(data_path, array_index).driver

    driver_var = driver.variables.new()
    driver_var.name = var_name
    driver_var.type = "SINGLE_PROP"
    driver_var.targets[0].id_type = target_id.id_type
    driver_var.targets[0].id = target_id
    driver_var.targets[0].data_path = target_data_path
    driver.expression = expression or driver_var.name

    return driver

