from typing import Generator

from bpy.types import Context, Event, Operator, Timer

from ..utils import GeneratorWithState


class AsyncOperator(Operator):
    _async_generator: GeneratorWithState[set[str], None, set[str]]
    _events_to_await: set[str]
    _timer: Timer | None

    def _run_async(self, context: Context) -> Generator[set[str], None, set[str]]:
        pass

    def _after_event(self, context: Context, event: Event):
        pass

    def _ended(self, context: Context):
        pass

    def _add_timer(self, context: Context, time_step: float):
        self._timer = context.window_manager.event_timer_add(time_step, window=context.window)

    def __poll_async_generator(self, context: Context) -> set[str]:
        next(self._async_generator, None)

        if self._async_generator.stopped:
            self.__remove_timer(context)
            self._ended(context)
            return self._async_generator.returned

        self._events_to_await = self._async_generator.last_yielded
        return {"RUNNING_MODAL"}

    def __remove_timer(self, context: Context):
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)

    def invoke(self, context: Context, _):
        self._timer = None
        self._async_generator = GeneratorWithState(self._run_async(context))

        first_result = self.__poll_async_generator(context)

        if first_result == {"RUNNING_MODAL"}:
            context.window_manager.modal_handler_add(self)

        return first_result

    def modal(self, context: Context, event: Event):
        if event.type not in self._events_to_await:
            return {"RUNNING_MODAL"}

        self._after_event(context, event)

        return self.__poll_async_generator(context)
