from manager import InputAudioManager # Supondo que salvou a classe neste arquivo
import time

def teste_monitoramento():
    manager = InputAudioManager()
    
    print("--- INICIANDO TESTE DE NOISE GATE ---")
    print("Use FONES DE OUVIDO para evitar microfonia.")
    print("Falando: Você deve ouvir sua voz.")
    print("Silêncio: O chiado de fundo deve sumir completamente.")
    print("Pressione CTRL+C para parar.")
    
    manager.start_input_stream()
    manager.start_output_stream()
    
    try:
        while True:
            # 1. Lê o chunk (o gate é aplicado aqui dentro)
            chunk = manager.read_chunk()
            
            # 2. Toca o chunk processado
            manager.write_chunk(chunk)
            
    except KeyboardInterrupt:
        print("\nTeste finalizado.")
    finally:
        manager.close()

if __name__ == "__main__":
    teste_monitoramento()