#!/usr/bin/env python3
"""
GPIO Edge Detection Test - Physical Pin 7 (BOARD mode)
Testa borda de subida e descida no pino físico 7.
Execute com: sudo python3 gpio_test_pin7.py
"""

import time
import sys

PIN = 7  # Pino físico (BOARD mode)

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
# 2. Limpeza prévia de estado
# ──────────────────────────────────────────────
print("[DEBUG] Limpando estado anterior do GPIO (GPIO.cleanup)...")
try:
    GPIO.cleanup()
    print("[DEBUG] GPIO.cleanup() executado com sucesso.")
except Exception as e:
    print(f"[AVISO] GPIO.cleanup() retornou erro (pode ser ignorado): {e}")

# ──────────────────────────────────────────────
# 3. Configuração do modo e do pino
# ──────────────────────────────────────────────
print(f"[DEBUG] Configurando modo BOARD...")
GPIO.setmode(GPIO.BOARD)
print(f"[DEBUG] Modo configurado: {GPIO.getmode()} (11 = BOARD)")

print(f"[DEBUG] Configurando pino {PIN} como INPUT com pull-up interno...")
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
print(f"[DEBUG] Pino {PIN} configurado.")

# ──────────────────────────────────────────────
# 4. Leitura inicial do estado
# ──────────────────────────────────────────────
estado_inicial = GPIO.input(PIN)
estado_str = "HIGH (1) - pino em repouso com pull-up" if estado_inicial == GPIO.HIGH else "LOW (0) - pino aterrado ou botão pressionado"
print(f"[DEBUG] Estado inicial do pino {PIN}: {estado_str}")

# ──────────────────────────────────────────────
# 5. Callback para detecção de borda
# ──────────────────────────────────────────────
press_time = {}

def on_edge(pin):
    estado = GPIO.input(pin)
    ts = time.strftime("%H:%M:%S")

    if estado == GPIO.LOW:
        # Borda de descida: sinal foi de HIGH → LOW (botão pressionado, com pull-up)
        press_time[pin] = time.time()
        print(f"\n[{ts}] ↓ BORDA DE DESCIDA no pino {pin}")
        print(f"         Estado: LOW (0) — botão PRESSIONADO")

    elif estado == GPIO.HIGH:
        # Borda de subida: sinal foi de LOW → HIGH (botão solto, com pull-up)
        duracao = 0.0
        if pin in press_time:
            duracao = (time.time() - press_time.pop(pin)) * 1000
        print(f"\n[{ts}] ↑ BORDA DE SUBIDA no pino {pin}")
        print(f"         Estado: HIGH (1) — botão SOLTO")
        print(f"         Duração do pressionamento: {duracao:.1f} ms")

# ──────────────────────────────────────────────
# 6. Registra detecção de borda (BOTH = subida e descida)
# ──────────────────────────────────────────────
print(f"\n[DEBUG] Registrando detecção de borda (BOTH) no pino {PIN}...")
try:
    GPIO.add_event_detect(
        PIN,
        GPIO.BOTH,
        callback=on_edge,
        bouncetime=50,  # 50ms debounce
    )
    print(f"[DEBUG] Detecção de borda registrada com sucesso no pino {PIN}.")
except RuntimeError as e:
    print(f"\n[ERRO] Falha ao registrar edge detection: {e}")
    print("       Causas comuns:")
    print("       1. Rode com sudo: sudo python3 gpio_test_pin7.py")
    print("       2. Usuário não está no grupo 'gpio': sudo usermod -a -G gpio $USER")
    print("       3. Pino já em uso por outro processo.")
    GPIO.cleanup()
    sys.exit(1)

# ──────────────────────────────────────────────
# 7. Loop principal — aguarda eventos
# ──────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"  Monitorando pino físico {PIN} (BOARD mode)")
print(f"  Pressione o botão para testar.")
print(f"  Ctrl+C para encerrar.")
print(f"{'='*50}\n")

try:
    while True:
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n\n[DEBUG] Interrompido pelo usuário (Ctrl+C).")

finally:
    print("[DEBUG] Executando GPIO.cleanup()...")
    GPIO.cleanup()
    print("[DEBUG] GPIO liberado. Encerrando.")