import wave
import audioop
import os


class WavReader:
    def __init__(self, target_rate: int, target_channels: int, chunk_size: int = 1024):
        """
        Configures the reader to deliver audio in the exact format required by the system.
        :param target_rate: E.g. 24000 (Hz)
        :param target_channels: E.g. 1 (Mono) or 2 (Stereo)
        :param chunk_size: Size of the read block (default 1024)
        """
        self.target_rate = target_rate
        self.target_channels = target_channels
        self.chunk_size = chunk_size

    def read_chunks(self, file_path: str):
        """
        Generator that reads the file and yields processed audio chunks.
        Automatically matches sample rate and channel configuration.
        """
        if not os.path.exists(file_path):
            print(f"[WavReader] File not found: {file_path}")
            return

        try:
            with wave.open(file_path, 'rb') as wf:
                file_rate = wf.getframerate()
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()

                while True:
                    frames = wf.readframes(self.chunk_size)
                    if not frames:
                        break

                    if file_rate != self.target_rate:
                        frames, _ = audioop.ratecv(
                            frames, sampwidth, n_channels, file_rate, self.target_rate, None
                        )

                    if n_channels != self.target_channels:
                        if n_channels == 2 and self.target_channels == 1:
                            frames = audioop.tomono(
                                frames, sampwidth, 0.5, 0.5)
                        elif n_channels == 1 and self.target_channels == 2:
                            frames = audioop.tostereo(frames, sampwidth, 1, 1)

                    yield frames

        except Exception as e:
            print(f"[WavReader] Error reading file: {e}")
