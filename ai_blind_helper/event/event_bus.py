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
        self.listeners[event_name].append(handler)

    def emit(self, event_name):

        if event_name not in self.listeners:
            return
 
        for handler in self.listeners[event_name]:
            if inspect.iscoroutinefunction(handler):
                if self.loop and self.loop.is_running():
                    asyncio.run_coroutine_threadsafe(handler(), self.loop)
                else:
                    print(f"Erro: Tentativa de rodar handler async {handler} sem loop ativo.")
            else:
                # Chamada síncrona normal
                handler()
                