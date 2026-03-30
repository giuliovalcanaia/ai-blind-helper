from manager import *
from config import Config
from keyboard import *

BINDS = {
PIN_1_1, PIN_1_2, PIN_1_3,
PIN_2_1, PIN_2_2, PIN_2_3,
PIN_3_1, PIN_3_2, PIN_3_3,
}

class ManagerProvider:
    def __init__(self):
        self.camera = CameraSource()
        # self.screen = ScreenSource()
        self.audio_input = InputAudioManager()
        self.audio_output = OutputAudioManager()
        # self.keyboard = KeyboardManager(Config.KEYBOARD_PATH)
        # To change to evdev, just replace the above line with:
        print(f"[ManagerProvider] Initializing GPIOKeyboardManager with pins: {BINDS}")
        self.keyboard = GPIOKeyboardManager(BINDS)
        
