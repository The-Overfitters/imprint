import dxcam
import time
from pynput.mouse import Button, Controller
from pynput import mouse
import cv2
import multiprocessing as mp
import warnings
import torch
import os

def bbox_from_xyxy(xyxy):
    return [int(xyxy['xmin']), int(xyxy['ymin']), int(xyxy['xmax']), int(xyxy['ymax'])]

def point_in_bbox(point, bbox):
    return (bbox[0] <= point[0] <= bbox[2]) and (bbox[1] <= point[1] <= bbox[3])

class Aimbot():
    def __init__(self):
        self.TOGGLE = False # For some reason button gets toggled so if we want to start on this should be False???
        self.shooting = False
        self.mouse_control = True
        print('[Aimbot] Init complete.')

    def on_click(self, x, y, button, pressed):
        if button == Button.x2 and pressed:
            self.TOGGLE = not self.TOGGLE
            print(f'[Aimbot] Toggled: {self.TOGGLE}')
        if button == Button.left and pressed and not self.shooting: # User editing or manually shooting
            self.mouse_control = False
        if button == Button.left and not pressed  and not self.shooting: # User stopped editing or manually shooting
            self.mouse_control = True
        self.mouse_buttons[button] = pressed

    def shoot(self):
        if not self.TOGGLE:
            return
        
        if self.mouse_control:
            self.mouse.press(Button.left)
            self.shooting = True

    def reset(self):
        if self.mouse_control and self.shooting:
            self.mouse.release(Button.left)
            self.shooting = False

    def run(self):
        bbox_queue = mp.Queue()
        
        shoot_flag = mp.Event() # Set when cursor on enemy
        reset_flag = mp.Event() # Set when new inference (similar to inference_flag, but cleared when we finish the reset func)

        self.mouse = Controller()
        self.mouse_buttons = {}

        inference_thread = mp.Process(target=self.inference_loop,
                                            args=[bbox_queue, reset_flag])
        bbox_check_thread = mp.Process(target=self.check_bbox_points,
                                            args=[bbox_queue, shoot_flag, self.mouse])

        mouse_thread = mouse.Listener(
            on_click = lambda x, y, button, pressed: self.on_click(x, y, button, pressed)
        )
        mouse_thread.start()

        inference_thread.start()
        bbox_check_thread.start()

        # Main thread program to handle Ctrl+C and force quit
        try:
            while True:
                if shoot_flag.is_set():
                    shoot_flag.clear()
                    self.shoot()
                if reset_flag.is_set():
                    reset_flag.clear()
                    self.reset()
                
                time.sleep(0.01)
        except KeyboardInterrupt:
            print("\nCtrl+C detected. Force quitting the program...")
            os._exit(1)  # Immediately terminate the program without any graceful shutdown

    def inference_loop(self, bbox_queue, callback_flag):
        #model = torch.hub.load('./yolo', 'custom', path='./yolo/weights/aimbot.pt', source='local', device=0 if torch.cuda.is_available() else 'cpu')
        model = torch.hub.load('./yolo', 'custom', path='./yolo/weights/aimbot.pt', source='local', device='cpu')
        model.eval()

        warnings.simplefilter(action='ignore', category=FutureWarning)

        camera = dxcam.create(output_idx=0)
        
        print('[Aimbot] Starting inference loop...')
        while True:
            start_time = time.time()  # Record the start time for FPS control
            
            frame = camera.grab()
            if frame is None:
                continue
            frame = cv2.cvtColor(cv2.resize(frame, (640,640)), cv2.COLOR_BGR2RGB)
            
            # Run inference
            results = model(frame)
            
            # Extract predictions
            predictions = results.pandas().xyxy
            if predictions is None or len(predictions) == 0:
                continue
            predictions = predictions[0]

            boxes = [bbox_from_xyxy(row) for _, row in predictions.iterrows()]
            

            bbox_queue.put(boxes)  # Add the latest bounding box
            callback_flag.set()

            # Sleep to maintain target FPS for inference
            elapsed_time = time.time() - start_time
            print(elapsed_time)
            sleep_time = max(0, 1/10 - elapsed_time)
            time.sleep(sleep_time)


    def check_bbox_points(self, bbox_queue, callback_flag, mouse):
        inference_mouse_pos = mouse.position
        shooting = False
        boxes = []
        
        print('[Aimbot] Starting bbox loop...')
        while True:
            start_time = time.time()  # Record the start time for FPS control

            # Check if a bounding box is available in the queue
            try:
                if not bbox_queue.empty(): # Just got new inference, reset shooting
                    boxes = bbox_queue.get_nowait()
                    inference_mouse_pos = mouse.position
                    shooting = False
                
                # There has not been a new bounding box drawn, so we should still keep shooting
                if shooting:
                    callback_flag.set()
                    continue
                
                mouse_delta = [(mouse.position[0] - inference_mouse_pos[0])*640/1920, -(mouse.position[1] - inference_mouse_pos[1])*640/1080]
                for box in boxes:
                    if point_in_bbox((320 + mouse_delta[0], 320 + mouse_delta[1]), box):
                        shooting = True
                        callback_flag.set()
                        continue
            
            except Exception as e:
                # Queue is empty (probably); no bounding box available
                continue

            elapsed_time = time.time() - start_time
            sleep_time = max(0, 1/60 - elapsed_time)
            time.sleep(sleep_time)
