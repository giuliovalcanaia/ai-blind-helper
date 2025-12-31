import io
import base64
import cv2
import PIL.Image
import mss
from abc import ABC, abstractmethod
from typing import Optional, Dict


class IVideoSource(ABC):
    """Interface abstrata para fontes de vídeo."""
    @abstractmethod
    def get_frame(self) -> Optional[Dict[str, str]]:
        pass

    @abstractmethod
    def release(self):
        pass


class CameraSource(IVideoSource):
    def __init__(self, camera_index=0):
        self.cap = None
        self.camera_index = camera_index

    def open(self):
        if self.cap is None or not self.cap.isOpened():
            print("[CameraSource open] Inicializando cv2.VideoCapture(0)...")
            self.cap = cv2.VideoCapture(self.camera_index)
        else:
            print("[CameraSource open] Câmera já estava aberta.")

    def get_frame(self) -> Optional[Dict[str, str]]:

        if self.cap is None or not self.cap.isOpened():
            print("[CameraSource get_frame] Câmera fechada detectada. Tentando abrir...")
            self.open()
            
             
        for _ in range(5):
            self.cap.grab()
        
        ret, frame = self.cap.read()
        if not ret:
            return None

        # Reduzir resolução (640px é suficiente para a IA entender o contexto)
        # O thumbnail anterior de 1024 era muito pesado
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(frame_rgb)
        # img.thumbnail([640, 640])  É USADO PARA DEIFINIR O TAMANHO DA CAPTURA, DO FRAME

        image_io = io.BytesIO()
        
        # OTIMIZAÇÃO CRÍTICA: quality=50 (padrão é 75-95)
        # optimize=True remove metadados inúteis
        img.save(image_io, format="jpeg", quality=50, optimize=True)
        image_io.seek(0)

        return {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(image_io.read()).decode()
        }

    def release(self):
        self.cap.release()


class ScreenSource(IVideoSource):
    def __init__(self, monitor_index=0):
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[monitor_index]

    def get_frame(self) -> Optional[Dict[str, str]]:
        sct_img = self.sct.grab(self.monitor)
        img = PIL.Image.frombytes(
            "RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        return {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(image_io.read()).decode()
        }

    def release(self):
        self.sct.close()
        self.cap = None
