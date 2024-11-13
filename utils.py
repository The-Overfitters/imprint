import os
import requests
import math

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
    @classmethod
    def from_values(cls, x1, y1, x2, y2):
        return cls(Point(x1, y1), Point(x2, y2))
    
    @classmethod
    def from_list(cls, l):
        return cls(Point(l[0], l[1]), Point(l[2], l[3]))

    def __init__(self, p1: Point, p2: Point):
        self.p1, self.p2 = p1, p2
        self.width, self.height = self.p2.x - self.p1.x, self.p2.y - self.p1.y
        self.midpoint = self.p1 + Point(self.width//2, self.height//2)
    
    def point_inside(self, point: Point):
        return (self.p1.x <= point.x <= self.p2.x) and (self.p1.y <= point.y <= self.p2.y)

    def __str__(self):
        return f"[({self.p1.x}, {self.p1.y}), ({self.p2.x}, {self.p2.y})]"

class Onion:
    def __init__(self):
        self.size = 10
        self.boxes = [None] * self.size
        self.expiry = 0

    def similarity(self, new: Box):
        eval = 0

        if self.boxes.count(None) == self.size: # Should never happen but just in case
            return 10000

        for i in range(self.size):
            if self.boxes[i] == None:
                break
            
            box: Box = self.boxes[i]
            weight = 1 - (i/self.size)**2

            area_eval =  1/100 * weight * abs(box.width * box.height - new.width * new.height)**2 # Maybe change area multiplier
            distance_eval = weight * math.sqrt((box.midpoint.x - new.midpoint.x)**2 + (box.midpoint.y - new.midpoint.y)**2)
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

def bbox_from_xyxy(xyxy):
    return [int(xyxy['xmin']), int(xyxy['ymin']), int(xyxy['xmax']), int(xyxy['ymax'])]

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