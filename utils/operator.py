from traceback import format_exc
from typing import Callable, ParamSpec, TypeAlias

from bpy.types import Context, Operator

from .result import ResultDoError

TArgs = ParamSpec("TArgs")
OperatorResult: TypeAlias = set[str]


def operator_do_execute(func: Callable[[Operator, Context], object]) -> Callable[[Operator, Context], OperatorResult]:
    def wrapper(operator: Operator, context: Context):
        try:
            return_value = func(operator, context)
            return return_value if return_value is not None else {"FINISHED"}
        except ResultDoError as do_error:
            error_message = str(do_error.value)
        except Exception as exception:
            error_message = format_exc(exception)
        operator.report({"ERROR"}, error_message)
        return {"CANCELLED"}

    return wrapper

