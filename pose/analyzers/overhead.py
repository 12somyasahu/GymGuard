from pose.utils import angle_between

def analyze(kp, angles, issues, spine_angle):
    ls = kp("left_shoulder");  le = kp("left_elbow");  lw = kp("left_wrist")
    rs = kp("right_shoulder"); re = kp("right_elbow"); rw = kp("right_wrist")

    l = angle_between(ls, le, lw)
    r = angle_between(rs, re, rw)
    if l: angles["left_elbow"]  = round(l, 1)
    if r: angles["right_elbow"] = round(r, 1)

    if spine_angle and spine_angle > 175:
        issues.append({
            "name": "Lumbar Hyperextension",
            "severity": round(min(1.0, (spine_angle - 175) / 15), 2),
            "message": "Lower back arching - disc compression risk"
        })