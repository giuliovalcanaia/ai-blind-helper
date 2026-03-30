import time
import threading
import RPi.GPIO as GPIO

DEFAULT_DEBOUNCE_TIME = 50

class GPIOKeyboardManager:
    def __init__(self, pins: list[int]):
        self._pins = pins
        print(f"[GPIOKeyboardManager __init__] Managed pins: {pins}")
        self._callbacks = {}
        self._active_keys = {}
        self._lock = threading.Lock()

    def register_key(self, pin: int, callback):
        if pin not in self._pins:
            raise ValueError(f"[GPIOKeyboardManager register_key] Pin {pin} not in managed pins list.")
        self._callbacks[pin] = callback
        print(f"[GPIOKeyboardManager register_key] Pin {pin} registered.")

    def start(self):
        try:
            GPIO.cleanup()
        except Exception as e:
            print(f"[GPIOKeyboardManager start] GPIO.cleanup() warning (can be ignored): {e}")

        GPIO.setmode(GPIO.BOARD)

        for pin in self._pins:
            print(f"[GPIOKeyboardManager start]: Setup for key {pin}")
            try:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(
                    pin,
                    GPIO.BOTH,
                    callback=self._on_event,
                    bouncetime=DEFAULT_DEBOUNCE_TIME
                )
            except Exception as e:
                print(f"[GPIOKeyboardManager start] Failed to configure pin {pin}: {e}")
                GPIO.cleanup()
                raise

        print(f"[GPIOKeyboardManager start] Listening on pins: {self._pins}")

    def stop(self):
        for pin in self._pins:
            GPIO.remove_event_detect(pin)
        GPIO.cleanup()
        print("[GPIOKeyboardManager] Stopped.")

    def _on_event(self, pin: int):
        if pin not in self._callbacks:
            return

        state = GPIO.input(pin)
        callback = self._callbacks[pin]

        with self._lock:
            if state == GPIO.LOW:
                self._active_keys[pin] = time.time()
                callback(event_type="PRESS", duration=0.0)
            elif state == GPIO.HIGH:
                start_time = self._active_keys.pop(pin, None)
                duration = 0.0
                if start_time is not None:
                    duration = (time.time() - start_time) * 1000
                callback(event_type="RELEASE", duration=duration)