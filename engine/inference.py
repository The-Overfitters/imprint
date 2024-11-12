import warnings
import dxcam
import time
import cv2

import utils
from yolo.models.common import AutoShape, DetectMultiBackend

class Inference():
    def __init__(self, bbox_queue, callback_flag, model_name):
        self.bbox_queue = bbox_queue
        self.callback_flag = callback_flag
        
        self.model = AutoShape(DetectMultiBackend(model_name, device='cpu'))
        self.model.eval()

        warnings.simplefilter(action='ignore', category=FutureWarning)

        self.camera = dxcam.create(output_idx=0)

        print('[Aimbot] Starting inference loop...')
        while True:
            self.inference_loop()
    
    def inference_loop(self, bbox_queue, callback_flag, model_name):
        start_time = time.time()  # Record the start time for FPS control
            
        frame = self.camera.grab()
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
        
        bbox_queue.put(boxes)  # Add the latest bounding box
        callback_flag.set()

        # Sleep to maintain target FPS for inference
        elapsed_time = time.time() - start_time
        sleep_time = max(0, 1/10 - elapsed_time)
        time.sleep(sleep_time)