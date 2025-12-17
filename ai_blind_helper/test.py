import evdev
import time
import sys

# --- CONFIGURAÇÃO ---
# Mude isso para o caminho do seu teclado (descubra com: ls -l /dev/input/by-id/)
# Exemplo: '/dev/input/event4' ou '/dev/input/by-id/seu-teclado-event-kbd'
CAMINHO_DO_TECLADO = '/dev/input/event13'
# --------------------


def main():
    try:
        device = evdev.InputDevice(CAMINHO_DO_TECLADO)
        print(f"Monitorando teclado: {device.name}")
        print("Pressione CTRL+C para sair.")
    except FileNotFoundError:
        print(f"Erro: Não encontrei o dispositivo {CAMINHO_DO_TECLADO}")
        return
    except PermissionError:
        print("Erro: Permissão negada. Rode com 'sudo'.")
        return

    # Dicionário para guardar o tempo de início
    teclas_pressionadas = {}

    # Loop que lê direto do Kernel
    for event in device.read_loop():
        if event.type == evdev.ecodes.EV_KEY:

            # Pega o nome da tecla (ex: KEY_A)
            key_name = evdev.ecodes.KEY.get(event.code, "DESCONHECIDO")

            # event.value 1 = Apertou
            if event.value == 1:
                if event.code not in teclas_pressionadas:
                    teclas_pressionadas[event.code] = time.time()
                    print(f"▼ Apertou: {key_name}")

            # event.value 0 = Soltou
            elif event.value == 0:
                if event.code in teclas_pressionadas:
                    inicio = teclas_pressionadas.pop(event.code)
                    duracao = time.time() - inicio
                    print(f"▲ Soltou:  {key_name} | Tempo: {duracao:.4f}s")
                    print("-" * 30)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass