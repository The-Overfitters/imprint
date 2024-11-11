# Imprint

This project is an automated aiming assistant that uses machine learning to detect targets in Fortnite and respond by simulating mouse input. It is configured to toggle and control aiming based on detected objects from a camera feed.

## Features

- Real-time target detection using YOLO-based object detection.
- Mouse input control for simulating aiming actions.
- Runs inference with specified bounding boxes and adjustable FPS.

## Requirements

- Python 3.8+
- Required libraries:
  - `dxcam`
  - `pynput`
  - `opencv-python`
  - `torch`

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/DlSCORD-unbIocked/imprint.git
cd imprint
```

### 2. Install Required Libraries
Use `pip` to install the required packages:
```bash
pip install -r requirments.txt
```

### 3. Download YOLO Weights
Ensure you have the YOLO weights file, `aimbot.pt`, saved in the `yolo/weights` directory. This will be downloaded automatically when running the main script if not present.

## Setup

1. Verify the path to your YOLO weights model in `main.py`:
   - By default, the model is expected to be downloaded from a URL specified in the `settings.py` file. Update this if necessary.
   
2. Configure any additional parameters in `aimbot.py` as needed.

## Running the Project

To start the aimbot, simply run `main.py`:

```bash
python main.py
```

### Controls
- **Toggle**: The aimbot can be toggled on and off by pressing the side button (`Button.x2`) on your mouse.
- **Manual Control**: You can manually shoot by pressing the left mouse button if you need to take control.

## File Overview

- **main.py**: Entry point of the program. Initializes and runs the `Aimbot` class.
- **aimbot.py**: Contains the main `Aimbot` class, which handles the object detection, bounding box checking, and mouse input.
- **utils.py**: Provides utility functions such as `download_file` to fetch YOLO weights.