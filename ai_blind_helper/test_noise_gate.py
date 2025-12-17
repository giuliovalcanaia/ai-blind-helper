from manager import InputAudioManager, OutputAudioManager
import time

def teste_monitoramento():
    input_manager = InputAudioManager()
    output_manager = OutputAudioManager()
    
    print("--- INICIANDO TESTE DE NOISE GATE ---")
    print("Use FONES DE OUVIDO para evitar microfonia.")
    print("Falando: Você deve ouvir sua voz.")
    print("Silêncio: O chiado de fundo deve sumir completamente.")
    print("Pressione CTRL+C para parar.")
    
    input_manager.start_input_stream()
    output_manager.start_output_stream()
    
    try:
        while True:
            # 1. Lê o chunk (o gate é aplicado aqui dentro)
            chunk = input_manager.read_chunk()
            
            # 2. Toca o chunk processado
            output_manager.write_chunk(chunk)
            
    except KeyboardInterrupt:
        print("\nTeste finalizado.")
    finally:
        input_manager.close()
        output_manager.close()

if __name__ == "__main__":
    teste_monitoramento()