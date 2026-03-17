from interface import *
from event import EventBus

class InterfaceProvider:
    def __init__(self, controller_provider, event_bus: EventBus):
        self.keyboard_interface = KeyboardInterface(event_bus=event_bus, keyboard_controller=controller_provider.keyboard, loop_controller=controller_provider.loop)