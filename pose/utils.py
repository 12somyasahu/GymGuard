import math
import numpy as np

KP = {
    "nose": 0, "left_eye": 1, "right_eye": 2, "left_ear": 3, "right_ear": 4,
    "left_shoulder": 5, "right_shoulder": 6,
    "left_elbow": 7, "right_elbow": 8,
    "left_wrist": 9, "right_wrist": 10,
    "left_hip": 11, "right_hip": 12,
    "left_knee": 13, "right_knee": 14,
    "left_ankle": 15, "right_ankle": 16,
}

def angle_between(a, b, c):
    if a is None or b is None or c is None:
        return None
    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    return math.degrees(math.acos(np.clip(cosine, -1.0, 1.0)))

def get_kp(keypoints, name, conf_thresh=0.2):
    idx = KP[name]
    if idx >= len(keypoints):
        return None
    kp = keypoints[idx]
    if len(kp) >= 3 and float(kp[2]) < conf_thresh:
        return None
    return (float(kp[0]), float(kp[1]))

def make_kp_func(keypoints):
    """Returns a simple kp(name) callable for a given keypoints array"""
    def kp(name):
        return get_kp(keypoints, name)
    return kp