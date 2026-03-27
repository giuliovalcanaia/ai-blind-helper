import io
import base64
import cv2
import PIL.Image
# import mss
from abc import ABC, abstractmethod
from typing import Optional, Dict


class IVideoSource(ABC):
    """Abstract interface for video sources."""
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
            print("[CameraSource open] Initializing cv2.VideoCapture(0)...")
            self.cap = cv2.VideoCapture(self.camera_index)
        else:
            print("[CameraSource open] Camera was already open.")

    def get_frame(self) -> Optional[Dict[str, str]]:

        if self.cap is None or not self.cap.isOpened():
            print("[CameraSource get_frame] Closed camera detected. Trying to open...")
            self.open()
            
             
        for _ in range(5):
            self.cap.grab()
        
        ret, frame = self.cap.read()
        if not ret:
            return None

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(frame_rgb)

        image_io = io.BytesIO()
        
        img.save(image_io, format="jpeg", quality=50, optimize=True)
        image_io.seek(0)

        return {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(image_io.read()).decode()
        }

    def release(self):
        self.cap.release()


# class ScreenSource(IVideoSource):
#     def __init__(self, monitor_index=0):
#         self.sct = mss.mss()
#         self.monitor = self.sct.monitors[monitor_index]

#     def get_frame(self) -> Optional[Dict[str, str]]:
#         sct_img = self.sct.grab(self.monitor)
#         img = PIL.Image.frombytes(
#             "RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

#         image_io = io.BytesIO()
#         img.save(image_io, format="jpeg")
#         image_io.seek(0)

#         return {
#             "mime_type": "image/jpeg",
#             "data": base64.b64encode(image_io.read()).decode()
#         }

#     def release(self):
#         self.sct.close()
#         self.cap = None
