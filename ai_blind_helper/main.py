import asyncio
import argparse
import sys
from config import (API_KEY)# Importa suas constantes

# Importa o controlador do pacote core
from core import LoopController 

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        type=str,
        default="camera",
        help="pixels to stream from",
        choices=["camera", "screen", "none"],
    )
    args = parser.parse_args()

    # Instancia passando a chave do config
    controller = LoopController(api_key=config.API_KEY, video_mode=args.mode)
    
    try:
        asyncio.run(controller.run())
    except KeyboardInterrupt:
        print("\nPrograma encerrado pelo usuário.")