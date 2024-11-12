import time
import utils
import math
from collections import namedtuple
from utils import Point, Box

class Tracker():
    def __init__(self, bbox_queue, callback_flag, mouse):
        self.bbox_queue = bbox_queue
        self.callback_flag = callback_flag
        self.mouse = mouse

        self.inference_mouse_pos = self.mouse.position
        self.shooting = False
        self.boxes: list[Box] = []
        self.onions: list[Onion] = []
        
        print('[Aimbot] Starting bbox loop...')
        while True:
            self.check_bbox_points()

    def check_bbox_points(self, ):
        start_time = time.time()  # Record the start time for FPS control

        # Check if a bounding box is available in the queue
        try:
            # TODO: Figure out what happens if there is more than one bbox in queue
            if not self.bbox_queue.empty(): # Just got new inference, reset shooting
                boxes = [Box(i) for i in self.bbox_queue.get_nowait()]
                inference_mouse_pos = self.mouse.position
                shooting = False
            
            # There has not been a new bounding box drawn, so we should still keep shooting
            if shooting:
                self.callback_flag.set()
                return
            
            mouse_delta = [(self.mouse.position[0] - inference_mouse_pos[0])*640/1920,
                           -(self.mouse.position[1] - inference_mouse_pos[1])*640/1080]
            for box in boxes:
                # Determine which onion to add to
                val, idx = min((val, idx) for (idx, val) in enumerate([o.similarity(box) for o in self.onions]))
                if val > 10000: # Tweak value, check for if we should make new onion or add
                    onion = Onion()
                    onion.add(box)
                    self.onions.append(onion)
                else:
                    self.onions[idx].add(box)

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

#TODO: Actually use this thing
class Onion:
    def __init__(self):
        self.size = 10
        self.boxes = [None] * self.size

    def similarity(self, new: Box):
        eval = 0

        if self.boxes.count(None) == self.size: # Should never happen but just in case
            return 10000

        for i in range(self.size):
            if self.boxes[i] == None:
                break
            
            box = self.boxes[i]
            weight = 1 - (i/len(self.size))**2

            area_eval =  1/100 * weight * abs(box.width * box.height - new.width * new.height)**2 # Maybe change area multiplier
            distance_eval = weight * math.sqrt((box.x - new.x)**2 + (box.y - new.y)**2)
            eval += area_eval + distance_eval

        # Average
        return eval / len([i for i in self.boxes if i is not None]) 


    def add(self, box: Box):
        # Shift elements to the right, dropping the last element
        self.boxes = [box] + self.boxes[:-1]

    def get(self, i) -> Box:
        if 0 <= i < self.size:
            return self.boxes[i]
        else:
            raise IndexError("Index out of bounds")