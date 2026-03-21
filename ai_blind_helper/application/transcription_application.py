import asyncio

class TranscriptionApplication:
    def __init__(self):
        print("[TranscriptionApplication __init__] Initializing transcription application and setting OCR prompt")
        
        self.prompt = "Transcribe all visible text in the image exactly as it appears, in a single audio-ready output with no formatting, extra symbols, or explanations."

    def get_prompt(self):
        print("[TranscriptionApplication get_prompt] Returning configured prompt for transcription")
        return self.prompt