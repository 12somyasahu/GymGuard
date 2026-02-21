from pose.utils import angle_between

def analyze(kp, angles, issues):
    lk = kp("left_knee");  la = kp("left_ankle")
    rk = kp("right_knee"); ra = kp("right_ankle")

    lk_a = angle_between(kp("left_hip"),  lk, la)
    rk_a = angle_between(kp("right_hip"), rk, ra)

    if lk_a: angles["left_knee"]  = round(lk_a, 1)
    if rk_a: angles["right_knee"] = round(rk_a, 1)

    if lk and la and lk[0] > la[0] + 25:
        issues.append({
            "name": "Left Knee Over Toe",
            "severity": round(min(1.0, (lk[0] - la[0] - 25) / 50), 2),
            "message": "Front knee too far forward - patellar tendon stress"
        })
    if rk and ra and rk[0] > ra[0] + 25:
        issues.append({
            "name": "Right Knee Over Toe",
            "severity": round(min(1.0, (rk[0] - ra[0] - 25) / 50), 2),
            "message": "Front knee too far forward - patellar tendon stress"
        })

    ls = kp("left_shoulder"); lh = kp("left_hip")
    if ls and lh and abs(ls[0] - lh[0]) > 40:
        issues.append({
            "name": "Torso Lean",
            "severity": round(min(1.0, (abs(ls[0] - lh[0]) - 40) / 60), 2),
            "message": "Torso leaning - maintain upright posture in lunge"
        })