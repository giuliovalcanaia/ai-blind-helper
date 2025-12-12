from google import genai
from config import Config


class GeminiClient:
    def __init__(self):
        self.client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=Config.API_KEY,
        )

    def connect(self):
        return self.client.aio.live.connect(model=Config.MODEL, config=Config.LIVE_CONFIG)
