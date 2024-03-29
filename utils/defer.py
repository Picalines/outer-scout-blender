import inspect
from functools import wraps


def defer(callback):
    for frame in inspect.stack():
        callee_locals = frame[0].f_locals
        if "__defers__" in callee_locals:
            callee_locals["__defers__"].append(callback)
            break


def with_defers(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        __defers__ = []
        try:
            return func(*args, **kwargs)
        finally:
            for callback in reversed(__defers__):
                callback()

    return wrapper

