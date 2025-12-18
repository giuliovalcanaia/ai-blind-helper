from manager import CameraSource, ScreenSource, InputAudioManager, KeyboardManager, OutputAudioManager
from config import Config

class ManagerProvider:
    def __init__(self):
        self.camera = CameraSource()
        self.screen = ScreenSource()
        self.audio_input = InputAudioManager()
        self.keyboard = KeyboardManager(Config.KEYBOARD_PATH)
        self.audio_output = OutputAudioManager()
        