from aimbot import Aimbot
from utils import download_file
from vars import DOWNLOAD_URL, DIRNAME, FILENAME # If this is erroring make sure to look at the README.md
import os

if __name__ == '__main__':
    download_file(DOWNLOAD_URL, DIRNAME, FILENAME)
    aimbot = Aimbot(os.path.join(DIRNAME, FILENAME))

    print('[main] Running aimbot...')
    aimbot.run()