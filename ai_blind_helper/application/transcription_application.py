import asyncio

class TranscriptionApplication:
    def __init__(self):
        print("[TranscriptionApplication __init__] Inicializando aplicação de transcrição e configurando prompt de OCR")
        
        self.prompt = (
            "Analise a imagem e transcreva todo o texto visível nela. "
        )

    def get_prompt(self):
        print("[TranscriptionApplication get_prompt] Retornando prompt configurado para transcrição")
        return self.prompt