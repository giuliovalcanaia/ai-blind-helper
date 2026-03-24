import asyncio
from manager import KeyboardManager
from config import Config

class GPIOKeyboardApplication:
    def __init__(self, gpio_keyboard_manager):
        print(f"[GPIOKeyboardApplication __init__] Initializing keyboard application with manager: {gpio_keyboard_manager}")
        self.gpio_keyboard_manager = gpio_keyboard_manager
        
    def start(self):
        print("[GPIOKeyboardApplication start] Requesting start of hardware monitoring via gpio_keyboard_manager")
        self.gpio_keyboard_manager.start()
        print("[GPIOKeyboardApplication start] Hardware monitoring started")
        
    def stop(self):
        print("[GPIOKeyboardApplication stop] Requesting stop of hardware monitoring")
        self.gpio_keyboard_manager.stop()
        print("[GPIOKeyboardApplication stop] Hardware monitoring stopped")
        
    def register_key(self, key_code, callback):
        print(f"[GPIOKeyboardApplication register_key] Binding key code {key_code} to provided callback")
        self.gpio_keyboard_manager.register_key(key_code, callback)
        print(f"[GPIOKeyboardApplication register_key] Key registration for {key_code} completed")
