import inspect
from functools import partial, wraps
from inspect import isgeneratorfunction
from typing import Any, Callable, ParamSpec

TParam = ParamSpec("TParam")


def defer(callback: Callable[TParam, Any], *args: TParam.args, **kwargs: TParam.kwargs):
    for frame in inspect.stack():
        callee_locals = frame[0].f_locals
        if "__defers__" in callee_locals:
            if len(args) > 0 or len(kwargs) > 0:
                callback = partial(callback, *args, **kwargs)

            callee_locals["__defers__"].append(callback)
            break


def with_defers(func):
    if isgeneratorfunction(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            __defers__ = []
            try:
                return (yield from func(*args, **kwargs))
            finally:
                for callback in reversed(__defers__):
                    callback()

    else:

        @wraps(func)
        def wrapper(*args, **kwargs):
            __defers__ = []
            try:
                return func(*args, **kwargs)
            finally:
                for callback in reversed(__defers__):
                    callback()

    return wrapper

