import asyncio
import traceback
from google import genai
from config import Config

class TextToSpeechApplication:
    def __init__(self, audio_output_queue: asyncio.Queue):
        """
        Inicializa o cliente para Text-to-Speech.
        :param audio_output_queue: A fila onde os chunks de áudio (bytes) devem ser depositados para reprodução.
        """
        print("[TextToSpeechApplication __init__] Inicializando cliente Gemini para TTS")
        self.client = genai.Client(api_key=Config.API_KEY)
        self.audio_output_queue = audio_output_queue

    async def run_tts(self, text: str):
        """
        Gera o áudio a partir do texto e coloca os dados brutos na fila de saída.
        """
        if not text:
            print("[TextToSpeechApplication run_tts] Aviso: Texto vazio recebido, ignorando.")
            return

        print(f"[TextToSpeechApplication run_tts] Iniciando geração de áudio para: '{text[:50]}...'")

        try:
            # Chama a API de forma assíncrona para não travar o loop principal
            response = await self.client.aio.models.generate_content(
                model=Config.TTS_MODEL,
                contents=text,
                config=Config.TTS_CONFIG
            )

            # Acessa os dados binários conforme o exemplo funcional fornecido
            # Caminho: candidates -> content -> parts -> inline_data -> data
            if response.candidates and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                
                if part.inline_data and part.inline_data.data:
                    audio_data = part.inline_data.data
                    size = len(audio_data)
                    
                    print(f"[TextToSpeechApplication run_tts] Áudio gerado com sucesso ({size} bytes). Enviando para fila.")
                    
                    # Coloca os bytes na fila para o player consumir (ex: PyAudio ou similar)
                    self.audio_output_queue.put_nowait(audio_data)
                else:
                    print("[TextToSpeechApplication run_tts] Erro: Resposta da API não contém dados de áudio (inline_data).")
            else:
                print("[TextToSpeechApplication run_tts] Erro: Estrutura de candidatos da resposta inválida.")

        except Exception as e:
            print(f"[TextToSpeechApplication run_tts] Erro crítico ao gerar TTS: {e}")
            traceback.print_exc()