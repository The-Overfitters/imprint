# Imprint

This project is an automated aiming assistant that uses machine learning to detect targets in Fortnite and respond by simulating mouse input. It is configured to toggle and control aiming based on detected objects from a camera feed.

## Features

- Real-time target detection using YOLO-based object detection.
- Mouse input control for simulating aiming actions.
- Runs inference with specified bounding boxes and adjustable FPS.

## Requirements

- Python 3.9+

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/DlSCORD-unbIocked/imprint.git
cd imprint
```

### 2. Install Required Libraries
Use `conda` or another env tool to organize the packages:
```bash
conda create -n imprint python=3.9
conda activate imprint
```
Install pytorch using pip from here: https://pytorch.org/get-started/locally/

Use `pip` to install the required packages:
```bash
pip install -r requirements.txt
```

### 3. Download YOLO Weights
Ensure you have the YOLO weights file, `aimbot.pt`, saved in the `yolo/weights` directory. This will be downloaded automatically when running the main script if not present.

## Setup

1. Create `vars.py` and add a DOWNLOAD_URL variable equal to your download link
   
2. Configure any additional parameters in `aimbot.py` as needed.

## Running the Project

To start the aimbot, simply run `main.py`:

```bash
python main.py
```

### Controls
- **Toggle**: The aimbot can be toggled on and off by pressing the front side button (`Button.x2`) on your mouse. This *can* be changed by editing `aimbot.py`
- **Manual Control**: You can manually shoot by pressing the left mouse button if you need to take control.

## File Overview

- **main.py**: Entry point of the program. Initializes and runs the `Aimbot` class.
- **aimbot.py**: Contains the main `Aimbot` class, which handles the object detection, bounding box checking, and mouse input.
- **utils.py**: Provides utility functions such as `download_file` to fetch YOLO weights.
