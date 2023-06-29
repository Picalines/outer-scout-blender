from typing import Generator, Any, TypeVar, Generic


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


TYield = TypeVar('TYield')
TSend = TypeVar('TSend')
TReturn = TypeVar('TReturn')


class GeneratorWithState(Generic[TYield, TSend, TReturn]):
    last_yielded: TYield | None
    returned: TReturn | None
    stopped: bool

    def __init__(self, generator: Generator[TYield, TSend, TReturn]) -> None:
        self._generator = generator
        self.last_yielded = None
        self.returned = None
        self.stopped = False

    def __iter__(self):
        return self

    def __next__(self):
        try:
            yielded = self.last_yielded = next(self._generator)
            return yielded
        except StopIteration as stop:
            self.returned = stop.value
            self.stopped = True
            raise
