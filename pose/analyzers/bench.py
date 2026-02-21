from pose.utils import angle_between

def analyze(kp, angles, issues):
    ls = kp("left_shoulder");  le = kp("left_elbow");  lh = kp("left_hip")
    rs = kp("right_shoulder"); re = kp("right_elbow"); rh = kp("right_hip")

    l_flare = angle_between(lh, ls, le)
    r_flare = angle_between(rh, rs, re)

    if l_flare: angles["L_flare"] = round(l_flare, 1)
    if r_flare: angles["R_flare"] = round(r_flare, 1)

    if l_flare and l_flare > 80:
        issues.append({
            "name": "Left Elbow Flare",
            "severity": round(min(1.0, (l_flare - 80) / 40), 2),
            "message": "Left elbow too wide - rotator cuff risk"
        })
    if r_flare and r_flare > 80:
        issues.append({
            "name": "Right Elbow Flare",
            "severity": round(min(1.0, (r_flare - 80) / 40), 2),
            "message": "Right elbow too wide - rotator cuff risk"
        })