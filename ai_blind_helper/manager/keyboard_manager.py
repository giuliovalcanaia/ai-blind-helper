import time
import evdev
import threading
def get_key_name(code):
    return evdev.ecodes.KEY.get(code, f"UNK_{code}")

class KeyboardManager:
    """
    Responsibility:
    - Read hardware (/dev/input/...)
    - Calculate key press duration
    - Manage the read thread
    - Call registered callbacks
    """
    def __init__(self, device_path):
        self.device_path = device_path
        self.device = None
        self.stop_event = threading.Event()
        self.listener_thread = None
        
        self.active_keys = {}
        
        self.callbacks = {}

    def register_key(self, key_code, callback):
        """
        The application uses this to indicate which keys it wants to listen to.
        The callback must accept: (event_type, duration)
        """
        self.callbacks[key_code] = callback
        print(f"[Manager] Key {get_key_name(key_code)} registered.")

    def start(self):
        """Start background listening."""
        try:
            self.device = evdev.InputDevice(self.device_path)
            self.listener_thread = threading.Thread(target=self._loop, daemon=True)
            self.listener_thread.start()
            print(f"[Manager] Listening on device: {self.device.name}")
        except FileNotFoundError:
            print(f"[Manager] ERROR: Device {self.device_path} not found.")
        except Exception as e:
            print(f"[Manager] ERROR starting: {e}")

    def stop(self):
        self.stop_event.set()

    def _loop(self):
        """Internal kernel read loop."""
        print("[Manager] Loop started.")
        
        try:
            for event in self.device.read_loop():
                if self.stop_event.is_set():
                    break
                
                if event.type == evdev.ecodes.EV_KEY:
                    self._process_event(event)
        except Exception as e:
            print(f"[Manager] Loop interrupted: {e}")

    def _process_event(self, event):
        if event.code not in self.callbacks:
            return

        callback = self.callbacks[event.code]

        if event.value == 1: 
            self.active_keys[event.code] = time.time()
            callback(event_type='PRESS', duration=0.0)

        elif event.value == 0:
            start_time = self.active_keys.pop(event.code, None)
            duration = 0.0
            if start_time:
                duration = (time.time() - start_time) * 1000
            
            # Notify the app that the key was released with the calculated duration
            callback(event_type='RELEASE', duration=duration)