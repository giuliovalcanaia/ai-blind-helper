import asyncio
import os
import time
import base64
from typing import Optional
from config import Config
import traceback

# Seus imports de aplicação
from application import (
    ClockApplication,
    LiveClientApplication,
    AudioPlayerApplication,
    VideoPlayerApplication,
    KeyboardApplication,
    DateApplication,
    DescriptionApplication,
    TranscriptionApplication,
    TextClientApplication,
    SystemMessageApplication
)

class MainController:
    def __init__(self, video_mode):
        # 1. Instanciação dos Sub-Sistemas
        self.clock_app = ClockApplication(language="pt")
        self.date_app = DateApplication(language="pt")
        self.msg_app = SystemMessageApplication(language="pt")
        self.gemini_client = LiveClientApplication()

        # Audio e Video
        self.audio_app = AudioPlayerApplication()
        self.video_app = VideoPlayerApplication(mode=video_mode)

        # Descrição e Transcrição
        self.description_app = DescriptionApplication()
        self.transcription_app = TranscriptionApplication()

        # Teclado
        self.keyboard_app = KeyboardApplication(
            controller=self, device_path=Config.KEYBOARD_PATH)

        # 2. Filas de comunicação
        self.audio_in_queue = asyncio.Queue()     # Recebe do Gemini
        self.out_queue = asyncio.Queue(maxsize=5)  # Envia para o Gemini

        # 3. Estado e Controle
        self.app_running = True
        self.session_task: Optional[asyncio.Task] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.audio_playback_task: Optional[asyncio.Task] = None

        # --- CONTROLE DE CAPTURA ---
        # Eventos (Portões)
        self.start_audio_event = asyncio.Event()
        self.start_video_event = asyncio.Event()

        # Tarefas atuais (para poder cancelar/parar especificamente a captura)
        self.current_audio_capture_task: Optional[asyncio.Task] = None
        self.current_video_capture_task: Optional[asyncio.Task] = None

    # --- PONTO DE ENTRADA ---
    def run(self):
        try:
            asyncio.run(self.start_main_loop())
        except KeyboardInterrupt:
            print("\n[Sistema] Interrupção detectada (CTRL+C).")
        finally:
            self.cleanup()

    # --- Callbacks do Teclado ---

    def handle_toggle_connect(self):
        """Tecla 'I': Conecta/Desconecta o WebSocket."""
        if self.loop is None:
            return

        if self.session_task and not self.session_task.done():
            print("\n[Comando] Tecla 'I': Encerrando conexão...")
            self.stop_session()
        else:
            print("\n[Comando] Tecla 'I': Conectando WebSocket...")
            # Garante que começa travado
            self.start_audio_event.clear()
            self.start_video_event.clear()

            asyncio.run_coroutine_threadsafe(
                self._start_connection_manager(), self.loop)

    def handle_quit(self):
        print("\n[Comando] Tecla Q: Saindo...")
        self.app_running = False
        self.stop_session()

    def stop_session(self):
        """
        Método síncrono chamado pelo Teclado (handle_toggle_connect) ou shutdown.
        Agenda a parada graciosa no Event Loop principal.
        """
        if self.loop is None:
            return

        print(">>> [Stop] Solicitando encerramento da sessão...")

        # 1. Trava capturas imediatamente (Thread-safe)
        self.loop.call_soon_threadsafe(self.start_audio_event.clear)
        self.loop.call_soon_threadsafe(self.start_video_event.clear)

        # 2. Agenda a corrotina de limpeza
        if self.session_task and not self.session_task.done():
            asyncio.run_coroutine_threadsafe(
                self._stop_session_task(), self.loop)

    async def _stop_session_task(self):
        """
        Lógica assíncrona real de parada.
        Cancela a TaskGroup e limpa resíduos de áudio.
        """
        if self.session_task:
            print(">>> [Stop] Cancelando TaskGroup da sessão...")
            self.session_task.cancel()
            try:
                # Aguarda o cancelamento propagar (vai disparar CancelledError no _run_session_lifecycle)
                await self.session_task
            except asyncio.CancelledError:
                # O erro é esperado aqui, pois acabamos de cancelar
                pass
            except Exception as e:
                print(f"[Erro] Falha ao aguardar cancelamento: {e}")
            finally:
                self.session_task = None

        # 3. Limpeza de filas (Opcional, mas recomendado)
        # Evita que áudio antigo toque quando você conectar novamente
        purged_count = 0
        while not self.audio_in_queue.empty():
            try:
                self.audio_in_queue.get_nowait()
                purged_count += 1
            except asyncio.QueueEmpty:
                break

        if purged_count > 0:
            print(f">>> [Limpeza] {
                  purged_count} itens de áudio removidos da fila.")

        print(">>> [Stop] Sessão encerrada e limpa.")

    def handle_time_request(self):
        if self.loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.play_current_time(), self.loop)

    def handle_date_request(self):
        if self.loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.play_current_date(), self.loop)

    # --- MÉTODOS DE CONTROLE DE FLUXO (START) ---

    def start_sending_audio_only(self):
        """Libera o fluxo de áudio."""
        print(">>> ATIVANDO: Apenas Áudio")
        if hasattr(self.audio_app, 'reset_buffer'):
            self.audio_app.reset_playback_state() 
        self.loop.call_soon_threadsafe(self.start_audio_event.set)
        # Opcional: Se quiser garantir que o vídeo pare ao ligar só áudio:
        # self.loop.call_soon_threadsafe(self.start_video_event.clear)

    def start_sending_audio_video(self):
        """Libera o fluxo de áudio E vídeo."""
        print(">>> ATIVANDO: Áudio + Vídeo")
        self.loop.call_soon_threadsafe(self.start_audio_event.set)
        self.loop.call_soon_threadsafe(self.start_video_event.set)

    def stop_sending_audio(self):
        """Pausa o envio de áudio (Hardware continua ligado, mas loop trava)."""
        print(">>> PAUSANDO: Áudio")
        self.loop.call_soon_threadsafe(self.start_audio_event.clear)

    def stop_sending_video(self):
        """Pausa o envio de vídeo (Hardware continua ligado, mas loop trava)."""
        print(">>> PAUSANDO: Vídeo")
        self.loop.call_soon_threadsafe(self.start_video_event.clear)

    def stop_all_sending(self):
        """Pausa tudo (modo mute/privacidade)."""
        print(">>> PAUSANDO: Tudo")
        self.stop_sending_audio()
        self.stop_sending_video()

    # --- Gerenciamento da Sessão ---

    async def _start_connection_manager(self):
        self.session_task = asyncio.create_task(self._run_session_lifecycle())

    async def _run_session_lifecycle(self):
        try:
            print(">>> WebSocket Conectado. Aguardando ativação de stream...")

            async with asyncio.TaskGroup() as tg:
                # 1. WebSocket Client
                tg.create_task(self.gemini_client.start_session(
                    input_queue=self.out_queue,
                    output_queue=self.audio_in_queue
                ))

                # 2. Wrappers de captura (Loops de monitoramento)
                tg.create_task(self._audio_capture_wrapper())
                tg.create_task(self._video_capture_wrapper())

        except asyncio.CancelledError:
            print(">>> Sessão encerrada.")
        except Exception as e:
            print(f"Erro na sessão: {e}")
        finally:
            # Limpeza da fila de saída
            while not self.out_queue.empty():
                try:
                    self.out_queue.get_nowait()
                except:
                    pass

    # --- NOVO HANDLER ---

    def handle_description_request(self):
        """Tecla 'D': Pede descrição usando a câmera já aberta."""
        if self.loop is None:
            return

        if not self.gemini_client.is_connected:
            print("\n[Aviso] Conecte-se ao Gemini (Tecla W) antes.")
            return

        print("\n[Comando] Tecla 'D': Solicitando descrição...")

        # Dispara a tarefa assíncrona
        asyncio.run_coroutine_threadsafe(
            self._send_description_task(), self.loop)

    async def _send_description_task(self):
        """Lógica de envio do prompt + snapshot"""

        # 1. Pega o frame da VideoApp existente, já retorna em BLOB/Dict
        # ASSUMIMOS que `frame_data` é um dicionário:
        # {"data": "base64_blob_aqui", "mime_type": "image/jpeg"}
        frame_data = await self.video_app.get_snapshot()

        if frame_data:
            try:
                os.makedirs("capturas", exist_ok=True)
                filename = f"capturas/snapshot_{int(time.time())}.jpg"
                b64_string = frame_data["data"]
                image_bytes = base64.b64decode(b64_string)
                with open(filename, "wb") as f:
                    f.write(image_bytes)
                print(f"[System] Imagem salva localmente em: {filename}")
            except Exception as e:
                print(f"[Erro] Falha ao salvar imagem: {e}")
            # -------------------------------------

            print("[System] Frame capturado. Enviando payload formatado para IA...")

            prompt_text = self.description_app.get_prompt()

            # --- CORREÇÃO AQUI ---
            # Passando o dicionário completo `frame_data` (que tem 'data' e 'mime_type')
            try:
                response_text = TextClientApplication.generate_text_by_imagem_text(
                    prompt=prompt_text,
                    image_part_data=frame_data  # Usando o nome do parâmetro da classe
                )
                print("\n\n>>> [Gemini Response] <<<")
                print(response_text)
                print(">>> ------------------- <<<")
                # Você pode adicionar a resposta para a fila de áudio se for um TTS, por exemplo
            except Exception as e:
                print(f"\n!!! [Gemini Error] Falha ao gerar texto: {e}")
                traceback.print_exc()

        else:
            print(
                "[Erro] Não foi possível capturar o frame (Câmera ocupada ou fechada).")

    def handle_transcription_request(self):
        """Tecla 'R': Reconhece texto e transcreve"""
        if self.loop is None:
            return

        if not self.gemini_client.is_connected:
            print("\n[Aviso] Conecte-se ao Gemini (Tecla W) antes.")
            return

        print("\n[Comando] Tecla 'R': Solicitando descrição...")

        # Dispara a tarefa assíncrona
        asyncio.run_coroutine_threadsafe(
            self._send_transcription_task(), self.loop)

    async def _send_transcription_task(self):
        """Lógica de envio do prompt + snapshot"""

        # 1. Pega o frame da VideoApp existente, já retorna em BLOB/Dict
        # ASSUMIMOS que `frame_data` é um dicionário:
        # {"data": "base64_blob_aqui", "mime_type": "image/jpeg"}
        frame_data = await self.video_app.get_snapshot()

        if frame_data:
            try:
                os.makedirs("capturas", exist_ok=True)
                filename = f"capturas/snapshot_{int(time.time())}.jpg"
                b64_string = frame_data["data"]
                image_bytes = base64.b64decode(b64_string)
                with open(filename, "wb") as f:
                    f.write(image_bytes)
                print(f"[System] Imagem salva localmente em: {filename}")
            except Exception as e:
                print(f"[Erro] Falha ao salvar imagem: {e}")
            # -------------------------------------

            print("[System] Frame capturado. Enviando payload formatado para IA...")

            prompt_text = self.transcription_app.get_prompt()

            # --- CORREÇÃO AQUI ---
            # Passando o dicionário completo `frame_data` (que tem 'data' e 'mime_type')
            try:
                response_text = TextClientApplication.generate_text_by_imagem_text(
                    prompt=prompt_text,
                    image_part_data=frame_data  # Usando o nome do parâmetro da classe
                )
                print("\n\n>>> [Gemini Response] <<<")
                print(response_text)
                print(">>> ------------------- <<<")
                # Você pode adicionar a resposta para a fila de áudio se for um TTS, por exemplo
            except Exception as e:
                print(f"\n!!! [Gemini Error] Falha ao gerar texto: {e}")
                traceback.print_exc()

        else:
            print(
                "[Erro] Não foi possível capturar o frame (Câmera ocupada ou fechada).")

    # --- WRAPPERS (MODIFICADOS) ---

    # A MUDANÇA CRUCIAL ESTÁ AQUI:
    # Passamos o evento para dentro da task, em vez de esperar por ele fora.

    async def _audio_capture_wrapper(self):
        print(">>> Inicializando loop de áudio (Aguardando flag...).")
        print(f"DEBUG: Controller Event ID: {id(self.start_audio_event)}")
        # Passamos o próprio evento (self.start_audio_event) para a função de captura
        await self.audio_app.task_capture_audio(self.out_queue, self.start_audio_event)

    async def _video_capture_wrapper(self):
        print(">>> Inicializando loop de vídeo (Aguardando flag...).")
        # Passamos o próprio evento (self.start_video_event) para a função de captura
        await self.video_app.task_capture_video(self.out_queue, self.start_video_event)

    # --- Funcionalidades Extras ---

    async def play_current_time(self):
        path = await asyncio.to_thread(self.clock_app.get_current_time_audio_path)
        if path:
            print(path)
            asyncio.create_task(self.audio_app.play_file(
                path, self.audio_in_queue, self.loop))

    async def play_current_date(self):
        # Agora chamamos o método novo (que retorna lista) e rodamos na thread
        paths = await asyncio.to_thread(self.date_app.get_current_date_audio_paths)

        if paths:
            print(f"[Sistema] Reproduzindo data: {len(paths)} arquivos.")
            for path in paths:
                # O 'await' aqui é crucial para garantir a ordem de inserção na fila
                # ou o início da task de reprodução na ordem correta
                await self.audio_app.play_file(path, self.audio_in_queue, self.loop)

                # Opcional: Um pequeno delay entre os áudios para não ficar encavalado
                # await asyncio.sleep(0.1)
        else:
            print("[Sistema] Nenhum áudio de data encontrado.")
            
    async def play_current_power_on_message(self):
        # O método get_current_welcome_message_path é rápido (só strings),
        # pode chamar direto sem thread ou await.
        path = self.msg_app.get_current_welcome_message_path()
        if path: 
            print(f"[Sistema] Reproduzindo Power On: {path}")
            # Toca o arquivo diretamente. NÃO use 'for', pois path é uma string única.
            await self.audio_app.play_file(path, self.audio_in_queue, self.loop)
        else:
            print("[Sistema] Nenhum áudio de power on encontrado.") 
    
    
    
    async def start_main_loop(self):
        self.loop = asyncio.get_running_loop()
        print("[Sistema] Iniciando monitor de teclado...")
        self.keyboard_app.start()

        self.audio_playback_task = asyncio.create_task(
            self.audio_app.task_play_audio(self.audio_in_queue)
        )

        await asyncio.create_task(self.play_current_power_on_message())

        # --- MENU VISUAL ATUALIZADO ---
        print("\n" + "="*45)
        print("      SISTEMA AI-BLIND-HELPER ONLINE      ")
        print("="*45)
        print(" [NAVEGAÇÃO MENU ROLÁVEL]")
        print("  < Esq >    : Navegar Anterior/Próximo")
        print("  [ENTER]    : Confirmar Opção Selecionada")
        print("-" * 45)
        print(" [ATALHOS GLOBAIS]")
        print("  [T]        : Data / Hora")
        print("  [A]        : Hold Áudio (Trava com duplo toque)")
        print("  [V]        : Hold Vídeo (Trava com duplo toque)")
        print("="*45 + "\n")

        while self.app_running:
            await asyncio.sleep(0.5)
        print("[Sistema] Loop encerrado.")

    def cleanup(self):
        if hasattr(self, 'keyboard_app'):
            self.keyboard_app.stop()
        if hasattr(self, 'audio_app'):
            self.audio_app.close()
        if hasattr(self, 'video_app'):
            self.video_app.release()

    def getWebSocketState(self):
        return self.gemini_client.is_connected()



    # --- CONTROLES DE PLAYBACK DE ÁUDIO ---

    def handle_audio_pause_toggle(self):
        """Tecla (Ex: Espaço ou P): Pausa/Continua a resposta da IA"""
        if hasattr(self.audio_app, 'toggle_pause'):
            self.audio_app.toggle_pause()

    def handle_audio_rewind(self):
        """Tecla (Ex: Seta Esquerda): Volta 5 segundos"""
        if hasattr(self.audio_app, 'rewind'):
            self.audio_app.rewind(seconds=5)

    def handle_audio_forward(self):
        """Tecla (Ex: Seta Direita): Avança 5 segundos"""
        if hasattr(self.audio_app, 'forward'):
            self.audio_app.forward(seconds=5)