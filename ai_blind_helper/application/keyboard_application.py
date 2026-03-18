import evdev
import asyncio
from manager import KeyboardManager
from config import Config

class KeyboardApplication:
    def __init__(self, keyboard_manager):
        print(f"[KeyboardApplication __init__] Initializing keyboard application with manager: {keyboard_manager}")
        self.keyboard_manager = keyboard_manager
        
    def start(self):
        print("[KeyboardApplication start] Requesting start of hardware monitoring via keyboard_manager")
        self.keyboard_manager.start()
        print("[KeyboardApplication start] Hardware monitoring started")
        
    def stop(self):
        print("[KeyboardApplication stop] Requesting stop of hardware monitoring")
        self.keyboard_manager.stop()
        print("[KeyboardApplication stop] Hardware monitoring stopped")
        
    def register_key(self, key_code, callback):
        print(f"[KeyboardApplication register_key] Binding key code {key_code} to provided callback")
        self.keyboard_manager.register_key(key_code, callback)
        print(f"[KeyboardApplication register_key] Key registration for {key_code} completed")
