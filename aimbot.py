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

    def run(self):
        bbox_queue = mp.Queue()
        gui_queue = mp.Queue()
        
        shoot_flag = mp.Event() # Set when cursor on enemy
        reset_flag = mp.Event() # Set when new inference

        self.mouse = Controller()
        self.mouse_buttons = {}
        

        # TODO: Inter-process communication so that tracker does shoot and reset, and reset_flag is passed directly from inference_thread
        inference_thread = mp.Process(target=Inference,
                                            args=[bbox_queue, self.model_name])
        tracker_thread = mp.Process(target=Tracker,
                                            args=[bbox_queue, gui_queue, self.mouse])

        inference_thread.start()
        tracker_thread.start()
        
        # Hacky GUI fix, temp testing
        app = QApplication(sys.argv)
        overlay = AimbotGUI(gui_queue)
        overlay.show()
        app.exec_() # Blocking, everything hangs after this

        # Main thread program to handle Ctrl+C and force quit
        try:
            while True:
                time.sleep(0.01)
        except KeyboardInterrupt:
            print("\nCtrl+C detected. Force quitting the program...")
            os._exit(1)  # Immediately terminate the program without any graceful shutdown
