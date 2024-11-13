import warnings
import dxcam
import time
import cv2
import torch

import win32gui
import win32ui
import win32con
import win32clipboard

import utils
from yolo.models.common import AutoShape, DetectMultiBackend

class Inference():
    def __init__(self, bbox_queue, model_name):
        self.bbox_queue = bbox_queue
        
        self.model = AutoShape(DetectMultiBackend(model_name, device=torch.device('cpu')))
        self.model.eval()

        warnings.simplefilter(action='ignore', category=FutureWarning)

        self.camera = dxcam.create(output_idx=0)

        self.run()
    
    def run(self):
        print('[Aimbot] Starting inference loop...')
        while True:
            self.inference_loop()

    # def capture(self):
    #     # Replace with the exact title of your application window
    #     win_name = "OBS - File Explorer"

    #     # https://stackoverflow.com/questions/48854815/bitmap-from-program-child-window-returns-as-black
    #     hWnd = win32gui.FindWindow(None, win_name)
    #     print(hWnd)
    #     windowcor = win32gui.GetWindowRect(hWnd)
    #     w=windowcor[2]-windowcor[0]
    #     h=windowcor[3]-windowcor[1]
    #     hDC=win32gui.GetDC(hWnd)
    #     memDC=win32gui.CreateCompatibleDC(hDC)
    #     hbmp = win32gui.CreateCompatibleBitmap(hDC, w, h)
    #     oldbmp = win32gui.SelectObject(memDC, hbmp)

    #     win32gui.BitBlt(memDC, 0,0,w, h, hDC, 0,0, win32con.SRCCOPY)
    #     win32gui.SelectObject(memDC, oldbmp)

    #     win32clipboard.OpenClipboard()
    #     win32clipboard.EmptyClipboard()
    #     win32clipboard.SetClipboardData(win32con.CF_BITMAP, hbmp.handle)
    #     win32clipboard.CloseClipboard()

    def inference_loop(self):
        start_time = time.time()  # Record the start time for FPS control
            
        frame = self.camera.grab()
        frame = self.capture()
        if frame is None:
            return
        frame = cv2.cvtColor(cv2.resize(frame, (640,640)), cv2.COLOR_BGR2RGB)
        
        # Run inference
        results = self.model(frame)
        
        # Extract predictions
        predictions = results.pandas().xyxy
        if predictions is None or len(predictions) == 0:
            return
        predictions = predictions[0]

        boxes = [utils.bbox_from_xyxy(row) for _, row in predictions.iterrows()]
        
        self.bbox_queue.put(boxes)  # Add the latest bounding box

        # Sleep to maintain target FPS for inference
        elapsed_time = time.time() - start_time
        sleep_time = max(0, 1/60 - elapsed_time)
        time.sleep(sleep_time)