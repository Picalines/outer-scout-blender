from typing import Generator, Any


def iter_recursive(dict_or_list: dict | list) -> Generator[tuple[Any, Any], None, None]:
    if isinstance(dict_or_list, dict):
        for key, value in dict_or_list.items():
            yield (key, value)

            if isinstance(value, (dict, list)):
                yield from iter_recursive(value)

    elif isinstance(dict_or_list, list):
        for i, item in enumerate(dict_or_list, start=0):
            yield (i, item)

            if isinstance(item, (dict, list)):
                yield from iter_recursive(item)
