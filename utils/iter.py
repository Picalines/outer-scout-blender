from typing import Any, Generator, Generic, Iterable, TypeVar

TItem = TypeVar("TItem")


def iter_with_prev(iterable: Iterable[TItem]) -> Generator[tuple[TItem | None, TItem], Any, None]:
    prev_item = None
    for item in iterable:
        yield (prev_item, item)
        prev_item = item


TYield = TypeVar("TYield")
TSend = TypeVar("TSend")
TReturn = TypeVar("TReturn")


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
