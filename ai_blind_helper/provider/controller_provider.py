from controller import *

class ControllerProvider:
    def __init__(self, application_provider, state_provider):
        self.audio = AudioController(application_provider.audio)
        self.keyboard = KeyboardController(application_provider.keyboard)
        self.language = LanguageController(application_provider.clock, application_provider.date, application_provider.system_msg)
        self.loop = LoopController(application_provider.audio, state_provider.loop, state_provider.app_running, application_provider.system_msg, state_provider.audio_in_queue, application_provider.keyboard, state_provider)
        self.time = TimeController(application_provider.clock, application_provider.date, application_provider.audio, state_provider.audio_in_queue, state_provider)
        self.sfx = AudioSFXController(application_provider.audio, state_provider.audio_in_queue, state_provider, application_provider.system_msg, application_provider.sfx)
        self.session = SessionController(application_provider.live_client, application_provider.video, application_provider.audio, state_provider.session_task, state_provider.out_queue, state_provider.audio_in_queue, state_provider.start_audio_event, state_provider.start_video_event, state_provider, self.sfx)
        self.description = DescritpionController(application_provider.video, application_provider.description, state_provider.loop)
        self.transcription = TranscriptionController(application_provider.video, application_provider.live_client, application_provider.transcription, state_provider.loop)
        self.menu = AudioMenuController(application_provider.audio, state_provider.audio_in_queue, state_provider, application_provider.menu)
        self.turn = TurnController(application_provider.live_client, application_provider.audio, state_provider.session_task, state_provider.out_queue, state_provider.audio_in_queue, state_provider.start_audio_event, state_provider, self.sfx)