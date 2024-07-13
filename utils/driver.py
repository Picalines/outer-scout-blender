from bpy.types import ID, bpy_struct


def add_driver(
    struct: bpy_struct, data_path: str, expression: str, *, array_index=-1, **variables: dict[str, tuple[ID, str]]
):
    driver = struct.driver_add(data_path, array_index).driver

    for name, (id, data_path) in variables.items():
        variable = driver.variables.new()
        variable.name = name
        variable.type = "SINGLE_PROP"
        variable_target = variable.targets[0]

        variable_target.id_type = id.id_type
        variable_target.id = id
        variable_target.data_path = data_path

    driver.expression = expression

    return driver
