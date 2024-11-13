import time
from pynput.mouse import Button
from utils import Box, Onion, Point
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from gui import AimbotGUI
from gui import GUIInfoPacket, GUIInfoType

class Tracker():
    def __init__(self, bbox_queue, gui_queue, mouse):
        self.bbox_queue, self.gui_queue = bbox_queue, gui_queue
        self.mouse = mouse
        self.TOGGLE = False

        self.inference_mouse_pos = self.mouse.position
        self.shooting = False
        self.boxes: list[Box] = []
        self.onions: list[Onion] = []

        self.run()

    def on_click(self, x, y, button, pressed):
        if button == Button.x2 and pressed:
            self.TOGGLE = not self.TOGGLE
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

        mouse_thread = self.mouse.Listener(
            on_click = lambda x, y, button, pressed: self.on_click(x, y, button, pressed)
        )
        mouse_thread.start()

        while True:
            self.check_bbox_points()
            self.gui_queue.put(GUIInfoPacket(GUIInfoType.ONION, self.onions))

    def check_bbox_points(self):
        start_time = time.time()  # Record the start time for FPS control

        # TODO: Figure out what happens if there is more than one bbox in queue
        if not self.bbox_queue.empty(): # Just got new inference, reset shooting
            self.boxes = [Box.from_list(i) for i in self.bbox_queue.get_nowait()]
            self.inference_mouse_pos = self.mouse.position
            self.reset()
        
        # There has not been a new bounding box drawn, so we should still keep shooting
        if self.shooting:
            self.shoot()
            return
        
        mouse_delta = [(self.mouse.position[0] - self.inference_mouse_pos[0])*640/1920,
                        -(self.mouse.position[1] - self.inference_mouse_pos[1])*640/1080]
        for box in self.boxes:
            # Determine which onion to add to
            val, idx = 1000000, None
            for i in range(len(self.onions)):
                self.onions[i].expiry += 1
                similarity = self.onions[i].similarity(box)

                if similarity < val:
                    val, i = similarity, i

            if val > 10000 or idx == None: # Tweak value, check for if we should make new onion or add
                onion = Onion()
                onion.add(box)
                self.onions.append(onion)
            else:
                self.onions[idx].add(box)
                self.onions[idx].expiry = 0
            
            self.onions = [i for i in self.onions if not i.expiry > 20] # Remove all onions that haven't recieved an inference in a while

            if box.point_inside(Point(320 + mouse_delta[0], 320 + mouse_delta[1])):
                self.shoot()
                return

        elapsed_time = time.time() - start_time
        sleep_time = max(0, 1/60 - elapsed_time)
        time.sleep(sleep_time)