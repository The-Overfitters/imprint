from pynput.mouse import Button, Controller
from pynput import mouse
import multiprocessing as mp
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from gui import AimbotGUI
import os
import time
import sys
from engine.inference import Inference
from engine.tracker import Tracker

class Aimbot():
    def __init__(self, model_name):
        self.model_name = model_name

        self.TOGGLE = False
        self.shooting = False

        print('[Aimbot] Init complete.')

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
        bbox_queue = mp.Queue()
        gui_queue = mp.Queue()
        
        shoot_flag = mp.Event() # Set when cursor on enemy
        reset_flag = mp.Event() # Set when new inference

        self.mouse = Controller()
        self.mouse_buttons = {}
        

        # TODO: Inter-process communication so that tracker does shoot and reset, and reset_flag is passed directly from inference_thread
        inference_thread = mp.Process(target=Inference,
                                            args=[bbox_queue, reset_flag, self.model_name])
        tracker_thread = mp.Process(target=Tracker,
                                            args=[bbox_queue, gui_queue, reset_flag, self.mouse])

        mouse_thread = mouse.Listener(
            on_click = lambda x, y, button, pressed: self.on_click(x, y, button, pressed)
        )
        mouse_thread.start()

        inference_thread.start()
        tracker_thread.start()
        
        # Hacky GUI fix, temp testing
        app = QApplication(sys.argv)
        overlay = AimbotGUI(gui_queue)
        overlay.show()
        app.exec_()
        timer = QTimer()
        timer.timeout.connect(lambda: None)  # No-op to keep the event loop active
        timer.start(16) # ms, make this fast (potentially faster), screw the gui no one cares

        # Main thread program to handle Ctrl+C and force quit
        try:
            while True:
                print('a')
                # TODO: Move this stuff into processes
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
