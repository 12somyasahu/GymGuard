from pose.utils import angle_between

def analyze(kp, angles, issues):
    ls = kp("left_shoulder");  le = kp("left_elbow");  lw = kp("left_wrist")
    rs = kp("right_shoulder"); re = kp("right_elbow"); rw = kp("right_wrist")
    lh = kp("left_hip");       rh = kp("right_hip")

    if ls and lh and rs and rh:
        avg_lean = ((lh[0] - ls[0]) + (rh[0] - rs[0])) / 2
        if avg_lean > 30:
            issues.append({
                "name": "Body Swing",
                "severity": round(min(1.0, (avg_lean - 30) / 60), 2),
                "message": "Using momentum - reduces bicep activation"
            })

    l_curl = angle_between(ls, le, lw)
    r_curl = angle_between(rs, re, rw)
    if l_curl: angles["left_curl"]  = round(l_curl, 1)
    if r_curl: angles["right_curl"] = round(r_curl, 1)