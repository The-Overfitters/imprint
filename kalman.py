import numpy as np
from filterpy.kalman import KalmanFilter

points = np.array([
    [1, 1],
    [1, 1],
    [1, 1],
])

kf = KalmanFilter(dim_x=4, dim_z=4)

kf.x = np.array(0, 0, 0, 0) # Initial state
dt = 1.0 # Time step of 1
kf.F = np.array([[1, dt, 0, 0], # Matrix for kinetmatic v_0*t + p, which we use for predictions
                 [0, 1, 0, 0],
                 [0, 0, 1, dt],
                 [0, 0, 0, 1]])
kf.H = np.Array([[1, 0, 0, 0], # Observe position and velocity from state matrix
                 [0, 1, 0, 0],
                 [0, 0, 1, 0],
                 [0, 0, 0, 1]])
kf.Q = np.eye(4) * 0.75 # Process noise - high due to unpredictability of players
kf.R = np.eye(4) * 0.01 # Measurment noise - low because we user accurate pixel measurments from bboxes
kf.P *= 1000 # Initial covariance matrix

# Process all known points
for point in points:
    kf.predict()
    kf.update(point)

kf.predict()
next_point = kf.x[:2] # Get position from state matrix
print(f'Predicted next point: {next_point}')