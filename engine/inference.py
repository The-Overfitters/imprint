import warnings
import dxcam
import time
import cv2
import torch
import numpy as np
import engine.onnx_inference as onnx_inference
import utils
import torch
from yolo.models.common import AutoShape, DetectMultiBackend


class Inference:
    def __init__(self, bbox_queue, model_name):
        self.bbox_queue = bbox_queue

        self.model = AutoShape(
            DetectMultiBackend(
                model_name,
                device=torch.device(0 if torch.cuda.is_available() else "cpu"),
            )
        )
        self.model.eval()

        warnings.simplefilter(action="ignore", category=FutureWarning)

        self.camera = dxcam.create(output_idx=1)

        session, input_details, input_size, confidence_threshold = (
            onnx_inference.setup()
        )
        self.session = session
        self.input_details = input_details
        self.input_size = input_size
        self.confidence_threshold = confidence_threshold

        self.run()

    def run(self):
        print("[Aimbot] Starting inference loop...")
        while True:
            self.inference_loop()

    def inference_loop(self, method="onnx"):
        start_time = time.time()  # Record the start time for FPS control

        frame = self.camera.grab()
        if frame is None:
            return
        frame = cv2.cvtColor(cv2.resize(frame, (640, 640)), cv2.COLOR_BGR2RGB)

        # Run inference

        if method == "onnx":
            boxes = []
            results, b = onnx_inference.inference(
                self.session,
                self.input_details,
                self.input_size,
                self.confidence_threshold,
                frame,
            )
            for box in b:
                x1, y1, width, height = map(int, box)
                width //= 3
                height //= 3
                boxes.append([x1 - width, y1 - height, x1 + width, y1 + height])
            # To visualize the results of onnx
            cv2.imshow("frame", results)
            cv2.waitKey(1)
        else:
            results = self.model(frame)

            # Extract predictions
            predictions = results.pandas().xyxy
            if predictions is None or len(predictions) == 0:
                return
            predictions = predictions[0]
            print("predict:", predictions)
            boxes = [utils.bbox_from_xyxy(row) for _, row in predictions.iterrows()]
            print("box:", boxes)
        # boxes = results
        self.bbox_queue.put(boxes)  # Add the latest bounding box

        # Sleep to maintain target FPS for inference
        elapsed_time = time.time() - start_time

        sleep_time = max(0, 1 / 60 - elapsed_time)
        time.sleep(sleep_time)
