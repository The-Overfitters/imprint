import os
import requests

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