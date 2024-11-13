import time
from pynput.mouse import Button
from pynput import mouse
from utils import Box, Onion, Point
from gui.gui import GUIInfoPacket, GUIInfoType

class Tracker():
    def __init__(self, bbox_queue, gui_queue, mouse):
        self.bbox_queue, self.gui_queue = bbox_queue, gui_queue
        self.mouse = mouse
        self.TOGGLE = False

        self.inference_mouse_pos = self.mouse.position
        self.mouse_buttons = {}
        self.shooting = False
        self.boxes: list[Box] = []
        self.onions: list[Onion] = []

        self.run()

    def on_click(self, x, y, button, pressed):
        if button == Button.x2 and pressed:
            self.TOGGLE = not self.TOGGLE
            self.gui_queue.put(GUIInfoPacket(GUIInfoType.TEXT, {'type': 'toggle', 'text': str(self.TOGGLE)}))
            print(f'[Aimbot] Toggled: {self.TOGGLE}')
        self.mouse_buttons[button] = pressed
    def shoot(self):
        if not self.TOGGLE:
            return
        
        self.mouse.press(Button.left)
        self.shooting = True
    def reset(self):
        if self.shooting:
            self.mouse.release(Button.left)
            self.shooting = False

    def run(self):
        print('[Aimbot] Starting bbox loop...')

        mouse_thread = mouse.Listener(
            on_click = lambda x, y, button, pressed: self.on_click(x, y, button, pressed)
        )
        mouse_thread.start()

        while True:
            self.check_bbox_points()
            self.gui_queue.put(GUIInfoPacket(GUIInfoType.ONION, self.onions))

    def check_bbox_points(self):
        start_time = time.time()  # Record the start time for FPS control

        reset_run = False

        # TODO: Figure out what happens if there is more than one bbox in queue
        if not self.bbox_queue.empty(): # Just got new inference, reset shooting
            self.boxes = [Box.from_list(i) for i in self.bbox_queue.get_nowait()]
            self.inference_mouse_pos = self.mouse.position
            reset_run = True
            self.reset()
        
        # There has not been a new bounding box drawn, so we should still keep shooting
        if self.shooting:
            self.shoot()
            return
        
        SENSITIVITY = 0.07 # Set to in-game sens
        mouse_delta = [(self.mouse.position[0] - self.inference_mouse_pos[0]) * SENSITIVITY, # Not true delta because we dampen it with sensitivity
                        -(self.mouse.position[1] - self.inference_mouse_pos[1]) * SENSITIVITY]
        
        used_onion_idx = []
        for box in self.boxes:
            box.p1 -= Point(mouse_delta[0], mouse_delta[1])
            box.p2 -= Point(mouse_delta[0], mouse_delta[1])

            if reset_run: # Determine which onion to add to
                val, idx = 1000000, None
                for i in range(len(self.onions)):
                    similarity = self.onions[i].similarity(box)

                    if similarity < val:
                        val, idx = similarity, i
                
                if val > 100 or idx == None: # Tweak value, check for if we should make new onion or add
                    onion = Onion()
                    onion.add(box)
                    self.onions.append(onion)
                    used_onion_idx.append(len(self.onions)-1)
                else:
                    self.onions[idx].add(box)
                    used_onion_idx.append(idx)

            # Shoot if hovering on real box or prediction
            valid_boxes = [box]
            if len(used_onion_idx) > 0:
                valid_boxes.extend(self.onions[used_onion_idx[-1]].predictions)
            for b in valid_boxes:
                if b.point_inside(Point(320, 320)):
                    self.shoot()
                    break
        
        if reset_run: # Remove all onions that haven't recieved an inference
            self.onions = [self.onions[i] for i in set(used_onion_idx)]
        
        elapsed_time = time.time() - start_time
        sleep_time = max(0, 1/60 - elapsed_time)
        time.sleep(sleep_time)