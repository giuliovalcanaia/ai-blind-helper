import sys
import tty
import termios
import threading
import select
import os


class KeyboardMonitor:
    def __init__(self):
        self._running = False
        self._thread = None
        self._callbacks = {}
        self._old_settings = None

    def register_callback(self, key, func):
        """Associa uma tecla a uma função."""
        self._callbacks[key] = func

    def start(self):
        """Inicia o monitoramento em uma thread separada."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop, name="KeyboardThread")
        self._thread.daemon = True  # Encerra a thread se o programa principal fechar
        self._thread.start()

    def stop(self):
        """Para o monitoramento e restaura o terminal."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join()

    def _run_loop(self):
        fd = sys.stdin.fileno()
        # Salva as configurações originais
        self._old_settings = termios.tcgetattr(fd)

        try:
            # Muda para modo RAW (sem buffer, sem echo)
            tty.setraw(fd)

            while self._running:
                # O select espera 0.1s para ver se tem input.
                # Se não tiver, o loop roda e verifica se self._running ainda é True.
                r, _, _ = select.select([sys.stdin], [], [], 0.1)

                if r:
                    ch = sys.stdin.read(1)

                    # Chama a função registrada se existir
                    if ch in self._callbacks:
                        # Executa a função associada à tecla
                        self._callbacks[ch]()

                    # Lógica interna de saída de emergência (opcional)
                    if ch == '\x03':  # Ctrl+C
                        self._running = False

        except Exception as e:
            print(f"Erro no monitor de teclado: {e}")

        finally:
            # RESTAURA O TERMINAL (Crítico!)
            termios.tcsetattr(fd, termios.TCSADRAIN, self._old_settings)
