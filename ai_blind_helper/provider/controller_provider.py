from controller import MainController

class ControllerProvider:
    def __init__(self, video_mode, application_provider):
        self.main_controller = MainController(application_provider.audio, application_provider.clock, application_provider.date, application_provider.description, application_provider.keyboard, application_provider.live_client, application_provider.system_msg, application_provider.text_client, application_provider.transcription, application_provider.video)