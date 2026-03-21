from event import (EventBus, KB_START, KB_STOP, KB_REGISTER)

class KeyboardController:
    def __init__(self, keyboard_application, event_bus: EventBus):
        print(f"[KeyboardController __init__] Initializing controller with keyboard_application: {keyboard_application}")
        self.keyboard_application = keyboard_application
        
        event_bus.subscribe(
            KB_START,
            self.start
        )
        
        event_bus.subscribe(
            KB_STOP,
            self.stop
        )
        
    def start(self):
        print("[KeyboardController start] Starting keyboard monitoring service")
        self.keyboard_application.start()
        print("[KeyboardController start] Keyboard service started successfully")
        
    def stop(self):
        print("[KeyboardController stop] Requesting keyboard service stop")
        self.keyboard_application.stop()
        print("[KeyboardController stop] Keyboard service stopped")

    def register_key(self, key_code, callback):
        print(f"[KeyboardController register_key] Registering callback for key: {key_code}")
        self.keyboard_application.register_key(key_code, callback)
        print(f"[KeyboardController register_key] Key {key_code} registered successfully")