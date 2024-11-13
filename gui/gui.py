import sys
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import QTimer
from utils import Box, Onion
import os
import signal
import enum

# Check if we are on Windows and import win32 if available
is_windows = sys.platform.startswith("win")
if is_windows:
    import win32con
    import win32gui

def box_to_screen_qrect(box: Box):
    return QRect(box.p1.x*1920/640, box.p1.y*1080/640, box.width*1920/640, box.height*1080/640)

class GUIInfoType(enum.Enum):
    ONION = 1
    TEXT = 2

class GUIInfoPacket():
    def __init__(self, type: GUIInfoType, data: any):
        self.type, self.data = type, data

class AimbotGUI(QMainWindow):
    def __init__(self, gui_queue):
        print('[Aimbot] Starting overlay...')
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setGeometry(0, 0, QApplication.primaryScreen().geometry().width(), QApplication.primaryScreen().geometry().height())

        self.gui_queue = gui_queue
        self.logo = QPixmap('gui/assets/imprint_logo_clear.png')
        self.info_text = QLabel('Initialized', self)
        self.info_text.move(90, 885)
        self.info_data = {}

        def handle_sigint(sig, frame):
            print("\nCtrl+C detected. Force quitting the program...")
            QApplication.quit()

        # Make sure we can actually control+c the stupid thing, and so main thread is not blocked - in the future it should be fine because ideally no work gets done here
        signal.signal(signal.SIGINT, handle_sigint)
        self.timer = QTimer()
        self.timer.timeout.connect(self.checkGUIUpdates)  # No-op to keep the event loop active
        self.timer.start(16) # ms, make this fast (potentially faster), screw the gui no one cares

        # Make the window truly click-through on Windows
        if is_windows:
            hwnd = int(self.winId())
            extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extended_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)

    def checkGUIUpdates(self):
        try:
            if not self.gui_queue.empty():
                self.repaint()
        except KeyboardInterrupt:
            print("\nCtrl+C detected. Force quitting the program...")
            QApplication.quit()
            os._exit(1)  # Immediately terminate the program without any graceful shutdown

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setBrush(Qt.BrushStyle.NoBrush)

        painter.drawPixmap(0, 825, self.logo.scaled(100, 100))

        while not self.gui_queue.empty():
            packet: GUIInfoPacket = self.gui_queue.get_nowait()
            render_style = 'partial' # or full. partial renders only prediction and current box
            
            if (packet.type == GUIInfoType.ONION):
                onions: list[Onion] = packet.data
                
                for onion in onions:
                    boxes = onion.boxes
                    if render_style == 'partial':
                        boxes = [boxes[0]]
                    for i, box in enumerate(boxes):
                        if box == None:
                            continue
                        transparency = max(0, int((onion.size - i)/float(onion.size) * 255.0))
                        painter.setPen(QPen(QColor(255, 0, 0, transparency), 2))
                        painter.drawRect(box_to_screen_qrect(box))

                    if onion.predictions[0] != None:
                        for pred in onion.predictions:
                            painter.setPen(QPen(QColor(0, 255, 0), 2))
                            painter.drawRect(box_to_screen_qrect(pred))
                        # painter.setPen(QPen(QColor(0, 0, 255), 2))
                        # painter.drawRect(box_to_screen_qrect(onion.predictions[1]))
            
            elif (packet.type == GUIInfoType.TEXT):
                self.info_data[packet.data['type']] = packet.data['text']
                self.info_text.setText(f"<font size='2' weight='bold'>{', '.join([f'{k}: {v}' for (k, v) in self.info_data.items()])}</font>")
        