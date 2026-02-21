import cv2

SKELETON = [
    (5, 6), (5, 7), (6, 8), (7, 9), (8, 10),
    (5, 11), (6, 12), (11, 12), (11, 13), (12, 14),
    (13, 15), (14, 16), (0, 5), (0, 6),
]

def draw_skeleton(frame, keypoints, risk_score):
    if risk_score < 30:
        color = (0, 230, 100)
    elif risk_score < 65:
        color = (30, 210, 255)
    else:
        color = (0, 60, 255)

    for a, b in SKELETON:
        if a >= len(keypoints) or b >= len(keypoints):
            continue
        ka, kb = keypoints[a], keypoints[b]
        if float(ka[2]) > 0.2 and float(kb[2]) > 0.2:
            cv2.line(frame,
                     (int(ka[0]), int(ka[1])),
                     (int(kb[0]), int(kb[1])),
                     color, 2, cv2.LINE_AA)

    for kp in keypoints:
        if float(kp[2]) > 0.2:
            cx, cy = int(kp[0]), int(kp[1])
            cv2.circle(frame, (cx, cy), 5, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(frame, (cx, cy), 5, color, 2, cv2.LINE_AA)

    return frame