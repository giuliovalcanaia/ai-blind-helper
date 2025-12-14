import pyaudio
import numpy as np
from config import Config

class InputAudioManager:
    def __init__(self):
        self.pya = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None
        
        # --- Configurações do Noise Gate ---
        self.threshold = 150  # Ajuste conforme necessário
        self.release_time = 0.5 # Segundos
        
        # Estado do Gate
        self.gate_open = False
        self.release_counter = 0
        
        # Calcula quantos chunks são necessários para o tempo de release
        # Fórmula: (Taxa de Amostragem / Tamanho do Chunk) * Tempo em Segundos
        if hasattr(Config, 'SEND_SAMPLE_RATE') and hasattr(Config, 'CHUNK_SIZE'):
            self.chunks_release = int(Config.SEND_SAMPLE_RATE / Config.CHUNK_SIZE * self.release_time)
        else:
            # Fallback caso a Config não esteja carregada no init ainda
            self.chunks_release = int(44100 / 1024 * self.release_time)

    def start_input_stream(self):
        mic_info = self.pya.get_default_input_device_info()
        self.input_stream = self.pya.open(
            format=Config.AUDIO_FORMAT,
            channels=Config.CHANNELS,
            rate=Config.SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=Config.CHUNK_SIZE,
        )

    def start_output_stream(self):
        self.output_stream = self.pya.open(
            format=Config.AUDIO_FORMAT,
            channels=Config.CHANNELS,
            rate=Config.RECEIVE_SAMPLE_RATE,
            output=True,
        )

    def read_chunk(self):
        """
        Lê o áudio do input, aplica o Noise Gate e retorna os bytes processados.
        """
        if not self.input_stream:
            return b''

        # 1. Leitura bruta
        raw_data = self.input_stream.read(Config.CHUNK_SIZE, exception_on_overflow=False)

        # 2. Processamento NumPy (Cálculo do RMS)
        audio_data = np.frombuffer(raw_data, dtype=np.int16)

        if len(audio_data) == 0:
            return raw_data

        # RMS: Raiz da média dos quadrados (convertendo para int64 para evitar overflow no quadrado)
        rms = int(np.sqrt(np.mean(audio_data.astype(np.int64)**2)))

        # 3. Lógica do Noise Gate
        if rms > self.threshold:
            # Som alto detectado: abre o gate e reseta o timer de release
            self.gate_open = True
            self.release_counter = 0
            return raw_data
        
        elif self.gate_open:
            # Som baixo, mas ainda estamos no tempo de "release" (segurando o gate aberto)
            self.release_counter += 1
            if self.release_counter > self.chunks_release:
                self.gate_open = False # Tempo acabou, fecha o gate
            return raw_data
        
        else:
            # Gate fechado: retorna silêncio absoluto
            return b'\x00' * len(raw_data)

    def write_chunk(self, data):
        if self.output_stream:
            self.output_stream.write(data)

    def close(self):
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
        self.pya.terminate()

    def closeInputs(self):
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()