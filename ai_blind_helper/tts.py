from google import genai
from google.genai import types
import wave
from config import Config

# Set up the wave file to save the output:
def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)

client = genai.Client(api_key=Config.API_KEY)

response = client.models.generate_content(
   model=Config.TTS_MODEL,
   contents="Diga em tom suave: describe surroundings",
   config=Config.TTS_CONFIG
)

data = response.candidates[0].content.parts[0].inline_data.data

file_name='out.wav'
wave_file(file_name, data) # Saves the file to current directory
