from event import (EventBus, KB_START, KB_STOP, KB_REGISTER)

class GPIOKeyboardController:
    def __init__(self, gpio_keyboard_application, event_bus: EventBus):
        print(f"[GPIOKeyboardController __init__] Initializing controller with gpio_keyboard_application: {gpio_keyboard_application}")
        self.gpio_keyboard_application = gpio_keyboard_application
        
        event_bus.subscribe(
            KB_START,
            self.start
        )
        
        event_bus.subscribe(
            KB_STOP,
            self.stop
        )
        
    def start(self):
        print("[GPIOKeyboardController start] Starting keyboard monitoring service")
        self.gpio_keyboard_application.start()
        print("[GPIOKeyboardController start] Keyboard service started successfully")
        
    def stop(self):
        print("[GPIOKeyboardController stop] Requesting keyboard service stop")
        self.gpio_keyboard_application.stop()
        print("[GPIOKeyboardController stop] Keyboard service stopped")

    def register_key(self, key_code, callback):
        print(f"[GPIOKeyboardController register_key] Registering callback for key: {key_code}")
        self.gpio_keyboard_application.register_key(key_code, callback)
        print(f"[GPIOKeyboardController register_key] Key {key_code} registered successfully")