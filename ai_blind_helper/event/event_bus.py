from collections import defaultdict
import asyncio
import inspect

class EventBus:

    def __init__(self, state_provider):
        self.listeners = defaultdict(list)
        
        @property
        def loop(self):
            return self.state_provider.loop

    def subscribe(self, event_name, handler):
        print(f"[EventBus subscribe] Subscribing handler {handler} to event '{event_name}'")
        self.listeners[event_name].append(handler)

    def emit(self, event_name):

        if event_name not in self.listeners:
            return
 
        for handler in self.listeners[event_name]:
            if inspect.iscoroutinefunction(handler):
                if self.loop and self.loop.is_running():
                    print(f"[EventBus emit] Emitting async event '{event_name}' to handler {handler} using loop {self.loop}")
                    asyncio.run_coroutine_threadsafe(handler(), self.loop)
                else:
                    print(f"[EventBus emit] Error: Event loop not available for async handler {handler} of event '{event_name}'")
            else:
                print(f"[EventBus emit] Emitting event '{event_name}' to handler {handler}")
                handler()
                