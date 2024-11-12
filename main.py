from aimbot import Aimbot
from utils import download_file
from vars import DOWNLOAD_URL
import os

if __name__ == '__main__':
    folder = 'yolo/weights'
    file = 'aimbot.pt'
    download_file(DOWNLOAD_URL, folder, file)
    aimbot = Aimbot(os.path.join(folder, file))

    print('[main] Running aimbot...')
    aimbot.run()