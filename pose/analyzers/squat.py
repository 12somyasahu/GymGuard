from pose.utils import angle_between

def analyze(kp, angles, issues):
    lk_a = angle_between(kp("left_hip"),  kp("left_knee"),  kp("left_ankle"))
    rk_a = angle_between(kp("right_hip"), kp("right_knee"), kp("right_ankle"))

    if lk_a: angles["left_knee"]  = round(lk_a, 1)
    if rk_a: angles["right_knee"] = round(rk_a, 1)

    lk = kp("left_knee");  la = kp("left_ankle")
    rk = kp("right_knee"); ra = kp("right_ankle")

    if lk and la and lk[0] > la[0] + 15:
        issues.append({
            "name": "Left Knee Valgus",
            "severity": round(min(1.0, (lk[0] - la[0] - 15) / 60), 2),
            "message": "Left knee caving inward - ACL/MCL strain risk"
        })
    if rk and ra and rk[0] < ra[0] - 15:
        issues.append({
            "name": "Right Knee Valgus",
            "severity": round(min(1.0, (ra[0] - rk[0] - 15) / 60), 2),
            "message": "Right knee caving inward - ACL/MCL strain risk"
        })