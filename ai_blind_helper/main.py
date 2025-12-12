import argparse
import asyncio
from application import Application
from keyboard_monitor import KeyboardMonitor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="camera",
                        choices=["camera", "screen", "none"])
    args = parser.parse_args()

    # 1. Instancia app
    app = Application(video_mode=args.mode)

    # 2. Configura Monitor de Teclado
    monitor = KeyboardMonitor()

    # Tecla V -> Chama a lógica que cria/cancela a task de conexão
    monitor.register_callback('v', app.handle_toggle_connect)

    # Tecla Q -> Seta a flag para sair do while e cancela tasks
    monitor.register_callback('q', app.handle_quit)

    # Tecla T: Fala a hora atual
    monitor.register_callback('t', lambda: asyncio.run_coroutine_threadsafe(
        app.play_current_time(), app.loop))

    print("=== CONTROLADOR GEMINI ===")
    print(" [V] - Conectar/Desconectar (Abre/Fecha Câmera)")
    print(" [T] - Fala a hora atual")
    print(" [Q] - Sair da aplicação")

    monitor.start()

    try:
        # 3. Roda o loop principal (que fica apenas esperando os comandos)
        asyncio.run(app.start_main_loop())
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop()


if __name__ == "__main__":
    main()
