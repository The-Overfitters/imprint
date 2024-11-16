import os
import requests
import math
import numpy as np
from filterpy.kalman import KalmanFilter

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
    
    def __truediv__(self, a):
        return Point(self.x / a, self.y / a)
    
    def __mul__(self, a):
        return Point(self.x * a, self.y * a)

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

class Box():
    @classmethod
    def from_values(cls, x1, y1, x2, y2):
        return cls(Point(x1, y1), Point(x2, y2))
    
    @classmethod
    def from_list(cls, l):
        return cls(Point(l[0], l[1]), Point(l[2], l[3]))

    @classmethod
    def from_midpoint(cls, midpoint: Point, width, height):
        return cls(midpoint + Point(-width//2, -height//2), midpoint + Point(width//2, height//2))

    def __init__(self, p1: Point, p2: Point):
        self.p1, self.p2 = p1, p2
        self.width, self.height = self.p2.x - self.p1.x, self.p2.y - self.p1.y
        self.midpoint = self.p1 + Point(self.width//2, self.height//2)
    
    def point_inside(self, point: Point):
        return (self.p1.x <= point.x <= self.p2.x) and (self.p1.y <= point.y <= self.p2.y)

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

class Onion:
    def __init__(self):
        self.size = 10
        self.boxes = [None] * self.size
        self.active_prediction = True
        self.predictions: list[Box] = [None, None]

    def similarity(self, new: Box):
        eval = 0

        if self.boxes.count(None) == self.size: # Should never happen but just in case
            return 10000

        for i in range(self.size):
            if self.boxes[i] == None:
                continue
            
            box: Box = self.boxes[i]
            weight = 1 - (i/self.size)**2

            # area_eval = 1/100 * weight * abs(box.width * box.height - new.width * new.height)**2 # Maybe change area multiplier
            area_eval = 0
            distance_eval = weight * math.sqrt((box.midpoint.x - new.midpoint.x)**2 + (box.midpoint.y - new.midpoint.y)**2)
            eval += area_eval + distance_eval

        # Average
        return eval / len([i for i in self.boxes if i is not None]) 

    def predict(self):
        self.predictions = kalman_prediction(self.boxes, n=3)

    def add(self, box: Box):
        # Shift elements to the right, dropping the last element
        self.boxes = [box] + self.boxes[:-1]
        if self.active_prediction:
            self.predict()
    
    def get(self, i) -> Box:
        if 0 <= i < self.size:
            return self.boxes[i]
        else:
            raise IndexError("Index out of bounds")
    
    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

def kalman_prediction(boxes: list[Box], n=1) -> Box:
    # Before: [0, n] -> [Newest, Oldest], After: [n, 0] -> [Oldest, Newest, with no None]
    points = [b.midpoint for b in boxes if b is not None] # Might want to change in future to make more sense (remove reverse)
    points.reverse()

    if len(points) == 0:
        return None

    kf = KalmanFilter(dim_x=4, dim_z=4)

    kf.x = np.array([points[0].x, 0, points[0].y, 0]) # Initial state
    dt = 1.0 # Time step of 1
    kf.F = np.array([[1, dt, 0, 0], # Matrix for kinetmatic v_0*t + p, which we use for predictions
                    [0, 1, 0, 0],
                    [0, 0, 1, dt],
                    [0, 0, 0, 1]])
    kf.H = np.array([[1, 0, 0, 0], # Observe position and velocity from state matrix
                    [0, 1, 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]])
    kf.Q = np.eye(4) * 0.75 # Process noise - high due to unpredictability of players
    kf.R = np.eye(4) * 0.01 # Measurment noise - low because we user accurate pixel measurments from bboxes
    kf.P *= 1000 # Initial covariance matrix

    # Process all known points
    for i in range(1, len(points)):
        if points[i] == None:
            continue
        kf.predict()
        vals = [points[i].x, points[i].x - points[i-1].x, points[i].y, points[i].y - points[i-1].y]
        kf.update(vals)

    predictions = []
    for i in range(n):
        kf.predict()
        next_midpoint = Point(kf.x[0], kf.x[2]) # Get position from state matrix
        next_width, next_height = boxes[0].width, boxes[0].height # Use width and height from newest box
        predictions.append(Box.from_midpoint(next_midpoint, next_width, next_height))
    
    return predictions

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