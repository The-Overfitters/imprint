from aimbot import Aimbot
from utils import download_file
from vars import DOWNLOAD_URL

if __name__ == '__main__':
    download_file(DOWNLOAD_URL, 'yolo/weights', 'aimbot.pt')
    aimbot = Aimbot()

    print('Running aimbot...')
    aimbot.run()