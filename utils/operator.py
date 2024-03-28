from functools import wraps
from inspect import isgeneratorfunction
from traceback import format_exc
from typing import Callable, TypeAlias

from bpy.types import Context, Operator

from .result import Result

OperatorResult: TypeAlias = set[str]


def operator_do(
    func: Callable[[Operator, Context], Result[object, object]]
) -> Callable[[Operator, Context], OperatorResult]:
    func = Result.do()(func)

    if isgeneratorfunction(func):

        @wraps(func)
        def wrapper(operator: Operator, context: Context):
            try:
                result = yield from func(operator, context)
                if result.is_error:
                    operator.report({"ERROR"}, str(result.unwrap_error()))
                    return {"CANCELLED"}
                status = result.unwrap()
                return status if status is not None else {"FINISHED"}
            except Exception as exception:
                operator.report({"ERROR"}, format_exc(exception))
                return {"CANCELLED"}

    else:

        @wraps(func)
        def wrapper(operator: Operator, context: Context):
            try:
                result = func(operator, context)
                if result.is_error:
                    operator.report({"ERROR"}, str(result.unwrap_error()))
                    return {"CANCELLED"}
                status = result.unwrap()
                return status if status is not None else {"FINISHED"}
            except Exception as exception:
                operator.report({"ERROR"}, format_exc(exception))
                return {"CANCELLED"}

    return wrapper

