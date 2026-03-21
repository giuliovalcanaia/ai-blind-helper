import asyncio
from typing import Optional

from manager import CameraSource 

class DescriptionApplication:
    def __init__(self):
        self.prompt = "Analyze the captured image now and describe the environment, objects, and context in detail."

    def get_prompt(self):
        return self.prompt