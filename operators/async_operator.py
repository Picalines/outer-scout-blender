from typing import Generator

from bpy.types import Operator, Context, Event

from ..utils import GeneratorWithState


class AsyncOperator(Operator):
    _async_generator: GeneratorWithState[set[str], None, set[str]]
    _events_to_await: set[str]

    def _run_async(self, context: Context) -> Generator[set[str], None, set[str]]:
        pass

    def _after_event(self, context: Context, event: Event):
        pass

    def _ended(self, context: Context):
        pass

    def _poll_async_generator(self, context: Context) -> set[str]:
        next(self._async_generator, None)

        if self._async_generator.stopped:
            self._ended(context)
            return self._async_generator.returned
        
        self._events_to_await = self._async_generator.last_yielded
        return {"RUNNING_MODAL"}

    def invoke(self, context: Context, _):
        self._async_generator = GeneratorWithState(self._run_async(context))

        context.window_manager.modal_handler_add(self)

        return self._poll_async_generator(context)
    
    def modal(self, context: Context, event: Event):
        if event.type not in self._events_to_await:
            return {"RUNNING_MODAL"}
        
        self._after_event(context, event)
        
        return self._poll_async_generator(context)
