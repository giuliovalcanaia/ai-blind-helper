import pyaudio
from config import Config

class OutputAudioManager:
    def __init__(self):
        print("[OutputAudioManager __init__] Inicializando gerenciador de saída de áudio (Hardware)")
        self.pya = pyaudio.PyAudio()
        self.output_stream = None

    def start_output_stream(self):
        print("[OutputAudioManager start_output_stream] Abrindo stream de reprodução para alto-falantes")
        try:
            self.output_stream = self.pya.open(
                format=Config.AUDIO_FORMAT,
                channels=Config.CHANNELS,
                rate=Config.RECEIVE_SAMPLE_RATE,
                output=True,
            )
            print(f"[OutputAudioManager start_output_stream] Saída de áudio ativada ({Config.RECEIVE_SAMPLE_RATE} Hz)")
        except Exception as e:
            print(f"[OutputAudioManager start_output_stream] Erro ao abrir stream de saída: {e}")

    def write_chunk(self, data):
        if self.output_stream:
            try:
                self.output_stream.write(data)
            except Exception as e:
                print(f"[OutputAudioManager write_chunk] Erro ao escrever no hardware de áudio: {e}")

    def close(self):
        print("[OutputAudioManager close] Finalizando hardware de saída")
        if self.output_stream:
            try:
                self.output_stream.stop_stream()
                self.output_stream.close()
                print("[OutputAudioManager close] Stream de saída fechado")
            except Exception as e:
                print(f"[OutputAudioManager close] Erro ao fechar stream: {e}")
        self.pya.terminate()
        print("[OutputAudioManager close] PyAudio finalizado")