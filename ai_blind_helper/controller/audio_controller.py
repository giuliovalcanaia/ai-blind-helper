import asyncio
from event import (EventBus, AUDIO_REWIND, AUDIO_FORWARD, AUDIO_PAUSE_TOGGLE)

class AudioController:
    
    def __init__(self, audio_app, event_bus: EventBus):
        print(f"[AudioController __init__] Initializing controller with audio_app: {audio_app}")
        self.audio_app = audio_app
        
        event_bus.subscribe(
            AUDIO_REWIND,
            self.handle_audio_rewind
        )
        
        event_bus.subscribe(
            AUDIO_FORWARD,
            self.handle_audio_forward
        )
        
        event_bus.subscribe(
            AUDIO_PAUSE_TOGGLE,
            self.handle_audio_pause_toggle
        )
    
    def handle_audio_pause_toggle(self):
        print("[AudioController handle_audio_pause_toggle] Attempting to toggle audio pause")
        if hasattr(self.audio_app, 'toggle_pause'):
            self.audio_app.toggle_pause()
            print("[AudioController handle_audio_pause_toggle] Toggle_pause command executed")

    def handle_audio_rewind(self):
        print("[AudioController handle_audio_rewind] Requesting rewind of 5 seconds")
        if hasattr(self.audio_app, 'rewind'):
            self.audio_app.rewind(seconds=5)
            print("[AudioController handle_audio_rewind] Rewind of 5 seconds completed")

    def handle_audio_forward(self):
        print("[AudioController handle_audio_forward] Requesting 5 second forward")
        if hasattr(self.audio_app, 'forward'):
            self.audio_app.forward(seconds=5)
            print("[AudioController handle_audio_forward] 5 second forward completed")