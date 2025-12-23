import argparse
import sys
from provider import *
from logger import *

def main():
    # INICIO DA GRAVAÇÃO: Deve ser a primeira coisa a rodar
    logger = TerminalLogger()
    logger.start()

    # Seu código original começa aqui
    state_provider = StateProvider()
    manager_provider = ManagerProvider()
    reader_provider = ReaderProvider()
    
    application_provider = ApplicationProvider(
        manager_provider=manager_provider, 
        reader_provider=reader_provider,
        state_provider=state_provider
    )
    
    controller_provider = ControllerProvider(
        application_provider=application_provider, 
        state_provider=state_provider
    )
    
    interface_provider = InterfaceProvider(controller_provider)

    application_provider.turn.set_interface(interface_provider.keyboard_interface)
    
    try:
        print("[Main main] Chamando interface_provider.keyboard_interface.run()")
        interface_provider.keyboard_interface.run()
    except KeyboardInterrupt:
        print("\n[Main main] Interrupção forçada via Terminal (SIGINT).")
        sys.exit(0)
    except Exception as e:
        # Esse bloco extra garante que erros inesperados também vão pro log
        print(f"\n[Main main] Erro fatal não tratado: {e}")
        raise # Relança o erro para aparecer o traceback completo no log 

if __name__ == "__main__":
    main()