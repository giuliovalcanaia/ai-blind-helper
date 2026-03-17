from interface import *
from event import EventBus

class InterfaceProvider:
    def __init__(self, controller_provider, event_bus: EventBus):
        self.keyboard_interface = KeyboardInterface(event_bus, controller_provider.loop, controller_provider.keyboard, controller_provider.session, controller_provider.language, controller_provider.time, controller_provider.transcription, controller_provider.description, controller_provider.audio, controller_provider.menu, controller_provider.sfx)