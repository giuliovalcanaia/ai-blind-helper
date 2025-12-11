import asyncio
import cv2
import mss
import PIL.Image
import io


class VideoCaptureManager:
    def __init__(self, mode="camera"):
        self.mode = mode
        self.cap = None
        self.sct = None

    async def setup(self):
        if self.mode == "camera":
            self.cap = await asyncio.to_thread(cv2.VideoCapture, 0)
        elif self.mode == "screen":
            self.sct = mss.mss()

    def _process_image(self, img_pil):
        """Redimensiona e converte para JPEG bytes"""
        img_pil.thumbnail([1024, 1024])
        image_io = io.BytesIO()
        img_pil.save(image_io, format="jpeg")
        image_io.seek(0)
        return image_io.read()

    def _get_camera_frame(self):
        ret, frame = self.cap.read()
        if not ret: return None
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return PIL.Image.fromarray(frame_rgb)

    def _get_screen_frame(self):
        monitor = self.sct.monitors[0]
        sct_img = self.sct.grab(monitor)
        return PIL.Image.fromarray(sct_img) # MSS retorna compativel com PIL

    async def get_frame_bytes(self):
        img = None
        if self.mode == "camera":
            img = await asyncio.to_thread(self._get_camera_frame)
        elif self.mode == "screen":
            img = await asyncio.to_thread(self._get_screen_frame)
        
        if img:
            return await asyncio.to_thread(self._process_image, img)
        return None

    def release(self):
        if self.cap: self.cap.release()