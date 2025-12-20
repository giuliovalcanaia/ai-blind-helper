import argparse
import sys
import os
from datetime import datetime
from provider import *

class TerminalLogger:
    """
    Captura todos os prints e erros do terminal e salva em arquivo,
    além de mostrar na tela.
    """
    def __init__(self, log_folder="logs"):
        # Cria a pasta de logs se não existir
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)

        # Cria nome do arquivo: logs/log_2025-12-19_10-30-00.txt
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = os.path.join(log_folder, f"log_{timestamp}.txt")
        
        # Abre o arquivo em modo append e guarda referência
        self.log_file = open(self.filename, "a", encoding="utf-8")
        self.terminal = sys.stdout # Guarda o terminal original
        
    def write(self, message):
        # Escreve na tela (terminal original)
        self.terminal.write(message)
        # Escreve no arquivo
        self.log_file.write(message)
        # Força salvar no disco imediatamente (útil se o programa travar)
        self.log_file.flush() 

    def flush(self):
        # Necessário para compatibilidade com o sistema
        self.terminal.flush()
        self.log_file.flush()

    def start(self):
        """Redireciona stdout e stderr para esta classe"""
        sys.stdout = self
        sys.stderr = self # Captura também erros (exceptions/tracebacks)
        print(f"--- [Logger] Gravando sessão em: {self.filename} ---")