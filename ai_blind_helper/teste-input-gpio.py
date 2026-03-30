#!/usr/bin/env python3
"""
GPIO Edge Detection Test - Multi-Pin (BOARD mode)
Testa borda de subida e descida em múltiplos pinos físicos.
Execute com: sudo python3 gpio_test_multi.py
"""

import time
import sys

# ──────────────────────────────────────────────
# 1. Verifica se RPi.GPIO está disponível
# ──────────────────────────────────────────────
print(f"[DEBUG] Python version: {sys.version}")

try:
    import RPi.GPIO as GPIO
    print(f"[DEBUG] RPi.GPIO importado com sucesso. Versão: {GPIO.VERSION}")
except ImportError as e:
    print(f"[ERRO] RPi.GPIO não encontrado: {e}")
    print("       Instale com: pip install RPi.GPIO --break-system-packages")
    sys.exit(1)

# ──────────────────────────────────────────────
# 2. Classe de Monitoramento GPIO
# ──────────────────────────────────────────────
class MonitorGPIO:
    def __init__(self):
        self.pinos = []
        self.press_time = {}

    def obter_entradas_usuario(self):
        """Coleta a quantidade e os números dos pinos via terminal."""
        try:
            qtd = int(input("\n[INPUT] Quantos pinos GPIO você deseja monitorar? "))
            if qtd <= 0:
                print("[ERRO] A quantidade deve ser maior que zero.")
                sys.exit(1)

            for i in range(qtd):
                pino = int(input(f"[INPUT] Digite o número do pino físico {i+1} (BOARD mode): "))
                if pino not in self.pinos:
                    self.pinos.append(pino)
                else:
                    print(f"[AVISO] Pino {pino} já foi adicionado. Ignorando duplicata.")
                    
        except ValueError:
            print("\n[ERRO] Entrada inválida! Por favor, insira apenas números inteiros.")
            sys.exit(1)

    def on_edge(self, pin):
        """Callback acionado na mudança de estado (borda) de qualquer pino configurado."""
        estado = GPIO.input(pin)
        ts = time.strftime("%H:%M:%S")

        if estado == GPIO.LOW:
            # Borda de descida: sinal foi de HIGH → LOW (botão pressionado, com pull-up)
            self.press_time[pin] = time.time()
            print(f"\n[{ts}] ↓ BORDA DE DESCIDA no pino {pin}")
            print(f"         Estado: LOW (0) — botão PRESSIONADO")

        elif estado == GPIO.HIGH:
            # Borda de subida: sinal foi de LOW → HIGH (botão solto, com pull-up)
            duracao = 0.0
            if pin in self.press_time:
                duracao = (time.time() - self.press_time.pop(pin)) * 1000
                
            print(f"\n[{ts}] ↑ BORDA DE SUBIDA no pino {pin}")
            print(f"         Estado: HIGH (1) — botão SOLTO")
            if duracao > 0:
                print(f"         Duração do pressionamento: {duracao:.1f} ms")

    def configurar_pinos(self):
        """Limpa o estado anterior, define o modo e configura cada pino."""
        print("\n[DEBUG] Limpando estado anterior do GPIO (GPIO.cleanup)...")
        try:
            GPIO.cleanup()
        except Exception as e:
            print(f"[AVISO] GPIO.cleanup() retornou erro (pode ser ignorado): {e}")

        print("[DEBUG] Configurando modo BOARD...")
        GPIO.setmode(GPIO.BOARD)

        for pino in self.pinos:
            print(f"\n[DEBUG] Configurando pino {pino} como INPUT com pull-up interno...")
            try:
                GPIO.setup(pino, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                
                # Leitura inicial do estado
                estado_inicial = GPIO.input(pino)
                estado_str = "HIGH (1) - repouso" if estado_inicial == GPIO.HIGH else "LOW (0) - pressionado"
                print(f"[DEBUG] Estado inicial do pino {pino}: {estado_str}")

                # Registra detecção de borda
                GPIO.add_event_detect(
                    pino,
                    GPIO.BOTH,
                    callback=self.on_edge,
                    bouncetime=50  # 50ms debounce
                )
                print(f"[DEBUG] Detecção de borda (BOTH) registrada no pino {pino}.")
                
            except Exception as e:
                print(f"[ERRO] Falha ao configurar o pino {pino}: {e}")
                GPIO.cleanup()
                sys.exit(1)

    def iniciar(self):
        """Inicia o loop principal de monitoramento."""
        self.obter_entradas_usuario()
        self.configurar_pinos()

        print(f"\n{'='*55}")
        print(f"  Monitorando os pinos físicos: {self.pinos}")
        print(f"  Pressione os botões para testar.")
        print(f"  Ctrl+C para encerrar.")
        print(f"{'='*55}\n")

        try:
            while True:
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n\n[DEBUG] Interrompido pelo usuário (Ctrl+C).")

        finally:
            print("[DEBUG] Executando GPIO.cleanup()...")
            GPIO.cleanup()
            print("[DEBUG] GPIO liberado. Encerrando.")

# ──────────────────────────────────────────────
# 3. Execução do Script
# ──────────────────────────────────────────────
if __name__ == "__main__":
    monitor = MonitorGPIO()
    monitor.iniciar()
