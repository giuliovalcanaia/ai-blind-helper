from application import *
from config import Config

class ApplicationProvider:
    def __init__(self, manager_provider, reader_provider):
        self.agenda = AgendaApplication()
        self.audio = AudioPlayerApplication(manager_provider.audio_input, manager_provider.audio_output, reader_provider.wav)
        self.clock = ClockApplication(Config.LANGUAGE)
        self.date = DateApplication(Config.LANGUAGE)
        self.description = DescriptionApplication()
        self.live_client = LiveClientApplication()
        self.system_msg = SystemMessageApplication(Config.LANGUAGE)
        self.text_client = TextClientApplication()
        self.keyboard = KeyboardApplication(keyboard_manager=manager_provider.keyboard)
        self.transcription = TranscriptionApplication()
        self.video = VideoRecorderApplication(Config.VIDEO_MODE, manager_provider.camera, manager_provider.screen)
        self.volume = VolumeControlApplication()
        self.menu = MenuApplication()
