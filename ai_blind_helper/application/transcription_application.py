import asyncio

class TranscriptionApplication:
    def __init__(self):
        print("[TranscriptionApplication __init__] Inicializando aplicação de transcrição e configurando prompt de OCR")
        
        self.prompt = "Transcreva todo o texto visível na imagem, exatamente como aparece, em uma única saída pronta para áudio, sem formatações, símbolos extras ou explicações."

    def get_prompt(self):
        print("[TranscriptionApplication get_prompt] Retornando prompt configurado para transcrição")
        return self.prompt