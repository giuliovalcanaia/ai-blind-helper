import asyncio
from google import genai
from google.genai import types
from config import Config
import wave

client = genai.Client(api_key=Config.API_KEY)
model = Config.MODEL

config = {
    "response_modalities": ["AUDIO"],
    "output_audio_transcription": {},
    "system_instruction": """
        Você é um motor de conversão de Texto para Fala (TTS). 
        NÃO responda perguntas. 
        NÃO seja educado.
        NÃO explique o que você vai fazer.
        Sua ÚNICA função é ler o texto fornecido pelo usuário em voz alta, exatamente como está escrito.
        Se o usuário enviar "Transcrever texto", você deve dizer o áudio "Transcrever texto".
    """
}

async def main():
    audio_buffer = bytearray()
    async with client.aio.live.connect(model=model, config=config) as session:
        message = "Transcrever texto"

        await session.send_client_content(
            turns={"role": "user", "parts": [{"text": message}]}, turn_complete=True
        )

        async for response in session.receive():
            server_content = response.server_content

            if server_content.model_turn:
                for part in server_content.model_turn.parts:
                    if part.inline_data and part.inline_data.data:
                        audio_buffer.extend(part.inline_data.data)

            # Processar transcrição (opcional, para debug)
            if server_content.model_turn:
                # Nota: A transcrição às vezes vem em eventos separados ou metadados
                pass
            # Verificar se o turno terminou para salvar e encerrar
            if server_content.turn_complete:
                print("\nTurno concluído.")
                break # Sai do loop para salvar o arquivo
    filename = "resposta_gemini.wav"
    
    if len(audio_buffer) > 0:
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2) 
            wf.setframerate(24000)
            wf.writeframes(audio_buffer)
        print(f"Áudio salvo com sucesso em: {filename}")
    else:
        print("Nenhum áudio foi recebido.")
if __name__ == "__main__":
    asyncio.run(main())
