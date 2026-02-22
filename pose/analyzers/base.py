import joblib
import numpy as np
from pathlib import Path
from pose.utils import angle_between, make_kp_func

# Load classifier if availabl
_clf = None
_le  = None
_MODEL_PATH = Path("models/exercise_classifier.pkl")
_LABEL_PATH = Path("models/label_encoder.pkl")

if _MODEL_PATH.exists() and _LABEL_PATH.exists():
    _clf = joblib.load(_MODEL_PATH)
    _le  = joblib.load(_LABEL_PATH)
    print("[INFO] Exercise classifier loaded")
else:
    print("[INFO] No classifier found - using heuristic detection")

# Rolling buffer for smoothing
_exercise_buffer = []
_BUFFER_SIZE = 12


def detect_exercise(kp, keypoints_raw, spine_angle, avg_knee, avg_elbow, wrists_high, hip_above_shoulder):
    global _exercise_buffer

    if _clf is not None and keypoints_raw is not None:
        flat = []
        for k in keypoints_raw:
            flat.append(float(k[0]) / 640)
            flat.append(float(k[1]) / 480)

        proba      = _clf.predict_proba([flat])[0]
        confidence = proba.max()
        predicted  = _le.classes_[proba.argmax()]

        if confidence > 0.6:
            _exercise_buffer.append(predicted)
    else:
        if hip_above_shoulder:
            predicted = "Bench Press"
        elif avg_knee and avg_knee < 120:
            predicted = "Squat"
        elif avg_knee and 120 <= avg_knee < 155:
            predicted = "Lunge"
        elif spine_angle and spine_angle < 140 and avg_knee and avg_knee >= 140:
            predicted = "Deadlift"
        elif wrists_high and avg_elbow and avg_elbow < 130:
            predicted = "Overhead Press"
        elif avg_elbow and avg_elbow < 100 and not wrists_high:
            predicted = "Bicep Curl"
        else:
            predicted = "Standing"

        _exercise_buffer.append(predicted)

    if len(_exercise_buffer) > _BUFFER_SIZE:
        _exercise_buffer.pop(0)

    if _exercise_buffer:
        return max(set(_exercise_buffer), key=_exercise_buffer.count)

    return "Standing"


def analyze_posture(keypoints):
    issues = []
    angles = {}
    kp = make_kp_func(keypoints)

    # Always-on checks
    spine_angle = (angle_between(kp("left_shoulder"),  kp("left_hip"),  kp("left_knee")) or
                   angle_between(kp("right_shoulder"), kp("right_hip"), kp("right_knee")))
    if spine_angle:
        angles["spine"] = round(spine_angle, 1)

    nose = kp("nose"); ls = kp("left_shoulder"); rs = kp("right_shoulder")
    if nose and ls and rs:
        offset = nose[0] - (ls[0] + rs[0]) / 2
        angles["neck_offset"] = round(offset, 1)
        if abs(offset) > 45:
            issues.append({
                "name": "Forward Head Posture",
                "severity": round(min(1.0, (abs(offset) - 45) / 80), 2),
                "message": "Head too far forward - cervical spine strain risk"
            })

    lk_a = angle_between(kp("left_hip"),  kp("left_knee"),  kp("left_ankle"))
    rk_a = angle_between(kp("right_hip"), kp("right_knee"), kp("right_ankle"))
    le_a = angle_between(kp("left_shoulder"),  kp("left_elbow"),  kp("left_wrist"))
    re_a = angle_between(kp("right_shoulder"), kp("right_elbow"), kp("right_wrist"))

    avg_knee  = ((lk_a or 0) + (rk_a or 0)) / max(1, int(bool(lk_a)) + int(bool(rk_a))) if (lk_a or rk_a) else None
    avg_elbow = ((le_a or 0) + (re_a or 0)) / max(1, int(bool(le_a)) + int(bool(re_a))) if (le_a or re_a) else None

    lw  = kp("left_wrist");    rw  = kp("right_wrist")
    ls2 = kp("left_shoulder"); rs2 = kp("right_shoulder")
    wrists_high = (lw and ls2 and lw[1] < ls2[1]) or (rw and rs2 and rw[1] < rs2[1])

    lh = kp("left_hip"); rh = kp("right_hip")
    hip_y = (((lh[1] if lh else 0) + (rh[1] if rh else 0)) /
              max(1, int(bool(lh)) + int(bool(rh)))) if (lh or rh) else 999
    sh_y  = (((ls2[1] if ls2 else 0) + (rs2[1] if rs2 else 0)) /
              max(1, int(bool(ls2)) + int(bool(rs2)))) if (ls2 or rs2) else 0

    exercise = detect_exercise(kp, keypoints, spine_angle, avg_knee, avg_elbow, wrists_high, hip_y < sh_y)

    # Route to analyzer
    from pose.analyzers import squat, deadlift, bench, lunge, curl, overhead

    if exercise == "Squat":
        squat.analyze(kp, angles, issues)
        if spine_angle and spine_angle < 145:
            issues.append({"name": "Excessive Forward Lean",
                           "severity": round(min(1.0, (145 - spine_angle) / 60), 2),
                           "message": "Torso too far forward - lower back risk"})
    elif exercise == "Deadlift":       deadlift.analyze(kp, angles, issues, spine_angle)
    elif exercise == "Bench Press":    bench.analyze(kp, angles, issues)
    elif exercise == "Lunge":          lunge.analyze(kp, angles, issues)
    elif exercise == "Bicep Curl":     curl.analyze(kp, angles, issues)
    elif exercise == "Overhead Press": overhead.analyze(kp, angles, issues, spine_angle)
    else:
        if spine_angle and spine_angle < 155:
            issues.append({"name": "Slouched Posture",
                           "severity": round(min(1.0, (155 - spine_angle) / 50), 2),
                           "message": "Maintain neutral spine"})

    risk_score = int(min(100, max([i["severity"] for i in issues]) * 70 + len(issues) * 10)) if issues else 0

    return {"issues": issues, "angles": angles, "risk_score": risk_score, "exercise_detected": exercise}