def analyze(kp, angles, issues, spine_angle):
    if spine_angle is not None and spine_angle < 130:
        issues.append({
            "name": "Spine Rounding",
            "severity": round(min(1.0, (130 - spine_angle) / 60), 2),
            "message": "Back rounding - serious lower back injury risk"
        })

    lw = kp("left_wrist")
    lh = kp("left_hip")
    if lw and lh and lw[0] - lh[0] > 40:
        issues.append({
            "name": "Bar Drift",
            "severity": round(min(1.0, (lw[0] - lh[0] - 40) / 80), 2),
            "message": "Bar drifting away from body - increases lower back load"
        })