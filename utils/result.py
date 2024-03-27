from contextlib import contextmanager
from typing import Callable, Generic, Never, NoReturn, ParamSpec, TypeVar

T = TypeVar("T")
E = TypeVar("E")
UT = TypeVar("UT")
UE = TypeVar("UE")
TArgs = ParamSpec("TArgs")


class ResultDoError(Exception):
    __slots__ = ("__value",)

    def __init__(self, value):
        self.__value = value

    @property
    def value(self):
        return self.__value


class Result(Generic[T, E]):
    __slots__ = ("__ok", "__value", "__error")

    def __init__(self, is_ok: bool, value: T | None, error: E | None) -> None:
        self.__ok = is_ok
        self.__value = value
        self.__error = error

    @staticmethod
    def ok(value: UT) -> "Result[UT, Never]":
        return Result(True, value, None)

    @staticmethod
    def error(error: UE) -> "Result[Never, UE]":
        return Result(False, None, error)

    @property
    def is_ok(self) -> bool:
        return self.__ok

    @property
    def is_error(self) -> bool:
        return not self.__ok

    def unwrap(self) -> T:
        if not self.is_ok:
            raise ValueError(f"{self.__class__.__name__} is error")
        return self.__value

    def unwrap_error(self) -> E:
        if self.is_ok:
            raise ValueError(f"{self.__class__.__name__} is ok")
        return self.__error

    def unwrap_or_else(self, func: Callable[[E], UT]) -> T | UT:
        return self.__value if self.is_ok else func(self.__error)

    def unwrap_or(self, default_value: UT) -> T | UT:
        return self.__value if self.is_ok else default_value

    def map(self, func: Callable[[T], UT]) -> "Result[UT, E]":
        return Result.ok(func(self.__value)) if self.is_ok else self

    def map_error(self, func: Callable[[E], UE]) -> "Result[T, UE]":
        return self if self.is_ok else Result.error(func(self.__error))

    def bind(self, func: "Callable[[T], Result[UT, UE]]") -> "Result[UT, E | UE]":
        return func(self.__value) if self.is_ok else self

    @staticmethod
    def do_error(value: UT) -> NoReturn:
        raise ResultDoError(value)

    def then(self) -> T:
        if not self.is_ok:
            self.do_error(self.__error)
        return self.__value

    def do(*, error: type[UE] = object) -> "Callable[[Callable[TArgs, UT]], Callable[TArgs, Result[UT, UE]]]":
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return_value = func(*args, **kwargs)
                except ResultDoError as do_error:
                    return_value = Result.error(do_error.value)
                if not isinstance(return_value, Result):
                    return_value = Result.ok(return_value)
                return return_value

            return wrapper

        return decorator

    @contextmanager
    @staticmethod
    def do_catch(exception_type: type[BaseException] = Exception):
        try:
            yield
        except BaseException as exception:
            if not isinstance(exception, exception_type):
                raise
            Result.do_error(exception)

    def __repr__(self) -> str:
        if self.is_ok:
            return f"Ok({self.__value!r})"
        return f"Error({self.__error!r})"

