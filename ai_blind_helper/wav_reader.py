import wave
import audioop
import os


class WavReader:
    def __init__(self, target_rate: int, target_channels: int, chunk_size: int = 1024):
        """
        Configura o leitor para entregar áudio no formato exato que o sistema exige.
        :param target_rate: Ex: 24000 (Hz)
        :param target_channels: Ex: 1 (Mono) ou 2 (Stereo)
        :param chunk_size: Tamanho do bloco de leitura (padrão 1024)
        """
        self.target_rate = target_rate
        self.target_channels = target_channels
        self.chunk_size = chunk_size

    def read_chunks(self, file_path: str):
        """
        Generator que lê o arquivo e devolve pedaços (chunks) de áudio processados.
        Compatibiliza automaticamente Sample Rate e Canais.
        """
        if not os.path.exists(file_path):
            print(f"[WavReader] Arquivo não encontrado: {file_path}")
            return

        try:
            with wave.open(file_path, 'rb') as wf:
                # Pega as propriedades originais do arquivo
                file_rate = wf.getframerate()
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()

                while True:
                    # Lê um pedaço bruto do arquivo
                    frames = wf.readframes(self.chunk_size)
                    if not frames:
                        break

                    # 1. Converte Taxa de Amostragem (Resample) se necessário
                    # Ex: Converte 44100Hz do arquivo para 24000Hz do sistema
                    if file_rate != self.target_rate:
                        frames, _ = audioop.ratecv(
                            frames, sampwidth, n_channels, file_rate, self.target_rate, None
                        )

                    # 2. Converte Canais (Mono <-> Stereo) se necessário
                    if n_channels != self.target_channels:
                        if n_channels == 2 and self.target_channels == 1:
                            frames = audioop.tomono(
                                frames, sampwidth, 0.5, 0.5)
                        elif n_channels == 1 and self.target_channels == 2:
                            frames = audioop.tostereo(frames, sampwidth, 1, 1)

                    # Devolve o pedaço de áudio pronto
                    yield frames

        except Exception as e:
            print(f"[WavReader] Erro ao ler arquivo: {e}")
