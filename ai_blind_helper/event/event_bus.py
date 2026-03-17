from collections import defaultdict
import asyncio

class EventBus:

    def __init__(self):
        self.listeners = defaultdict(list)

    def subscribe(self, event_name, handler):
        self.listeners[event_name].append(handler)

    async def emit(self, event_name, data=None):

        if event_name not in self.listeners:
            return
 
        for handler in self.listeners[event_name]:
            result = handler(data)

            if asyncio.iscoroutine(result):
                await result 