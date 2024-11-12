import time
import utils

class Tracker():
    def __init__(self, bbox_queue, callback_flag, mouse):
        self.bbox_queue = bbox_queue
        self.callback_flag = callback_flag
        self.mouse = mouse

        self.inference_mouse_pos = self.mouse.position
        self.shooting = False
        self.boxes = []
        
        print('[Aimbot] Starting bbox loop...')
        while True:
            self.check_bbox_points()

    def check_bbox_points(self, ):
        start_time = time.time()  # Record the start time for FPS control

        # Check if a bounding box is available in the queue
        try:
            # TODO: Figure out what happens if there is more than one bbox in queue
            if not self.bbox_queue.empty(): # Just got new inference, reset shooting
                boxes = self.bbox_queue.get_nowait()
                inference_mouse_pos = self.mouse.position
                shooting = False
            
            # There has not been a new bounding box drawn, so we should still keep shooting
            if shooting:
                self.callback_flag.set()
                return
            
            mouse_delta = [(self.mouse.position[0] - inference_mouse_pos[0])*640/1920,
                           -(self.mouse.position[1] - inference_mouse_pos[1])*640/1080]
            for box in boxes:
                if utils.point_in_bbox((320 + mouse_delta[0], 320 + mouse_delta[1]), box):
                    shooting = True
                    self.callback_flag.set()
                    return
        
        except Exception as e:
            # Queue is empty (probably); no bounding box available
            return

        elapsed_time = time.time() - start_time
        sleep_time = max(0, 1/60 - elapsed_time)
        time.sleep(sleep_time)