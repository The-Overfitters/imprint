import os
import requests

class Point():
    def __init__(self, x, y):
        self.x, self.y = x, y
    
    def __add__(self, a):
        if isinstance(a, Point):
            return Point(self.x + a.x, self.y + a.y)
        else:
            return Point(self.x + a, self.y + a)
        
    def __sub__(self, a):
        if isinstance(a, Point):
            return Point(self.x - a.x, self.y - a.y)
        else:
            return Point(self.x - a, self.y - a)

class Box():
    def __init__ (self, x1, y1, x2, y2):
        return self.__init__(Point(x1, y1), Point(x2, y2))

    def __init__(self, p1: Point, p2: Point):
        self.p1, self.p2 = p1, p2
        self.width, self.height = self.p2.x - self.p1.x, self.p2.y - self.p1.y
        self.midpoint = Point(self.p1 + Point(self.width//2, self.height//2))

def bbox_from_xyxy(xyxy):
    return [int(xyxy['xmin']), int(xyxy['ymin']), int(xyxy['xmax']), int(xyxy['ymax'])]

def point_in_bbox(point, bbox):
    return (bbox[0] <= point[0] <= bbox[2]) and (bbox[1] <= point[1] <= bbox[3])

def download_file(url, directory, filename):
    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)
    
    file_path = os.path.join(directory, filename)
    
    if os.path.isfile(file_path):
        print(f"File already exists: {file_path}")
        return file_path
    
    # Download the file
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Downloaded: {file_path}")
    else:
        print(f"Failed to download: {url} (status code {response.status_code})")
        return None
    
    return file_path