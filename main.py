import cv2
import numpy as np
import base64
import asyncio
import json
import math
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from pathlib import Path

# --- GPU-accelerated YOLOv8 Pose shakitaman model it is  -------------------------------------------
try:
    from ultralytics import YOLO
    import torch
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[INFO] Using device: {DEVICE}")

    model = YOLO("yolov8m-pose.pt")

    # Warm-up pass — no manual .half(), ultralytics handles precision internally
    dummy = np.zeros((480, 640, 3), dtype=np.uint8)
    model(dummy, verbose=False, device=DEVICE)
    print("[INFO] GPU warm-up complete")

    YOLO_AVAILABLE = True
    print("[INFO] YOLOv8m-Pose ready")
except Exception as e:
    print(f"[WARN] YOLOv8 not available: {e}")
    YOLO_AVAILABLE = False
    DEVICE = "cpu"

app = FastAPI(title="GymGuard")

KP = {
    "nose": 0, "left_eye": 1, "right_eye": 2, "left_ear": 3, "right_ear": 4,
    "left_shoulder": 5, "right_shoulder": 6,
    "left_elbow": 7, "right_elbow": 8,
    "left_wrist": 9, "right_wrist": 10,
    "left_hip": 11, "right_hip": 12,
    "left_knee": 13, "right_knee": 14,
    "left_ankle": 15, "right_ankle": 16,
}

SKELETON = [
    (5, 6), (5, 7), (6, 8), (7, 9), (8, 10),
    (5, 11), (6, 12), (11, 12), (11, 13), (12, 14),
    (13, 15), (14, 16), (0, 5), (0, 6),
]

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

def analyze_squat(kp, angles, issues):
    lk_a = angle_between(kp("left_hip"),  kp("left_knee"),  kp("left_ankle"))
    rk_a = angle_between(kp("right_hip"), kp("right_knee"), kp("right_ankle"))
    if lk_a: angles["left_knee"]  = round(lk_a, 1)
    if rk_a: angles["right_knee"] = round(rk_a, 1)
    lk = kp("left_knee");  la = kp("left_ankle")
    rk = kp("right_knee"); ra = kp("right_ankle")
    if lk and la and lk[0] > la[0] + 15:
        sev = min(1.0, (lk[0] - la[0] - 15) / 60)
        issues.append({"name": "Left Knee Valgus", "severity": round(sev, 2),
                       "message": "Left knee caving inward - ACL/MCL strain risk"})
    if rk and ra and rk[0] < ra[0] - 15:
        sev = min(1.0, (ra[0] - rk[0] - 15) / 60)
        issues.append({"name": "Right Knee Valgus", "severity": round(sev, 2),
                       "message": "Right knee caving inward - ACL/MCL strain risk"})

def analyze_deadlift(kp, angles, issues, spine_angle):
    if spine_angle is not None and spine_angle < 130:
        sev = min(1.0, (130 - spine_angle) / 60)
        issues.append({"name": "Spine Rounding", "severity": round(sev, 2),
                       "message": "Back rounding - serious lower back injury risk"})
    lw = kp("left_wrist"); lh = kp("left_hip")
    if lw and lh and lw[0] - lh[0] > 40:
        sev = min(1.0, (lw[0] - lh[0] - 40) / 80)
        issues.append({"name": "Bar Drift", "severity": round(sev, 2),
                       "message": "Bar drifting away from body - increases lower back load"})

def analyze_bench(kp, angles, issues):
    ls = kp("left_shoulder"); le = kp("left_elbow"); lh = kp("left_hip")
    rs = kp("right_shoulder"); re = kp("right_elbow"); rh = kp("right_hip")
    l_flare = angle_between(lh, ls, le)
    r_flare = angle_between(rh, rs, re)
    if l_flare: angles["L_flare"] = round(l_flare, 1)
    if r_flare: angles["R_flare"] = round(r_flare, 1)
    if l_flare and l_flare > 80:
        issues.append({"name": "Left Elbow Flare", "severity": round(min(1.0,(l_flare-80)/40),2),
                       "message": "Left elbow too wide - rotator cuff risk"})
    if r_flare and r_flare > 80:
        issues.append({"name": "Right Elbow Flare", "severity": round(min(1.0,(r_flare-80)/40),2),
                       "message": "Right elbow too wide - rotator cuff risk"})

def analyze_lunge(kp, angles, issues):
    lk = kp("left_knee");  la = kp("left_ankle")
    rk = kp("right_knee"); ra = kp("right_ankle")
    lk_a = angle_between(kp("left_hip"),  lk, la)
    rk_a = angle_between(kp("right_hip"), rk, ra)
    if lk_a: angles["left_knee"]  = round(lk_a, 1)
    if rk_a: angles["right_knee"] = round(rk_a, 1)
    if lk and la and lk[0] > la[0] + 25:
        issues.append({"name": "Left Knee Over Toe", "severity": round(min(1.0,(lk[0]-la[0]-25)/50),2),
                       "message": "Front knee too far forward - patellar tendon stress"})
    if rk and ra and rk[0] > ra[0] + 25:
        issues.append({"name": "Right Knee Over Toe", "severity": round(min(1.0,(rk[0]-ra[0]-25)/50),2),
                       "message": "Front knee too far forward - patellar tendon stress"})

def analyze_curl(kp, angles, issues):
    ls = kp("left_shoulder"); le = kp("left_elbow"); lw = kp("left_wrist")
    rs = kp("right_shoulder"); re = kp("right_elbow"); rw = kp("right_wrist")
    lh = kp("left_hip"); rh = kp("right_hip")
    if ls and lh and rs and rh:
        avg_lean = ((lh[0]-ls[0]) + (rh[0]-rs[0])) / 2
        if avg_lean > 30:
            issues.append({"name": "Body Swing", "severity": round(min(1.0,(avg_lean-30)/60),2),
                           "message": "Using momentum - reduces bicep activation"})
    l_curl = angle_between(ls, le, lw)
    r_curl = angle_between(rs, re, rw)
    if l_curl: angles["left_curl"]  = round(l_curl, 1)
    if r_curl: angles["right_curl"] = round(r_curl, 1)

def analyze_ohp(kp, angles, issues, spine_angle):
    ls = kp("left_shoulder"); le = kp("left_elbow"); lw = kp("left_wrist")
    rs = kp("right_shoulder"); re = kp("right_elbow"); rw = kp("right_wrist")
    l = angle_between(ls, le, lw)
    r = angle_between(rs, re, rw)
    if l: angles["left_elbow"]  = round(l, 1)
    if r: angles["right_elbow"] = round(r, 1)
    if spine_angle and spine_angle > 175:
        issues.append({"name": "Lumbar Hyperextension", "severity": round(min(1.0,(spine_angle-175)/15),2),
                       "message": "Lower back arching - disc compression risk"})

def analyze_posture(keypoints):
    issues = []
    angles = {}

    def kp(name):
        return get_kp(keypoints, name)

    spine_angle = angle_between(kp("left_shoulder"), kp("left_hip"), kp("left_knee")) or \
                  angle_between(kp("right_shoulder"), kp("right_hip"), kp("right_knee"))
    if spine_angle:
        angles["spine"] = round(spine_angle, 1)

    nose = kp("nose"); ls = kp("left_shoulder"); rs = kp("right_shoulder")
    if nose and ls and rs:
        offset = nose[0] - (ls[0]+rs[0])/2
        angles["neck_offset"] = round(offset, 1)
        if abs(offset) > 45:
            issues.append({"name": "Forward Head Posture",
                           "severity": round(min(1.0,(abs(offset)-45)/80),2),
                           "message": "Head too far forward - cervical spine strain risk"})

    lk_a = angle_between(kp("left_hip"),  kp("left_knee"),  kp("left_ankle"))
    rk_a = angle_between(kp("right_hip"), kp("right_knee"), kp("right_ankle"))
    le_a = angle_between(kp("left_shoulder"),  kp("left_elbow"),  kp("left_wrist"))
    re_a = angle_between(kp("right_shoulder"), kp("right_elbow"), kp("right_wrist"))

    avg_knee  = ((lk_a or 0)+(rk_a or 0)) / max(1, int(bool(lk_a))+int(bool(rk_a))) if (lk_a or rk_a) else None
    avg_elbow = ((le_a or 0)+(re_a or 0)) / max(1, int(bool(le_a))+int(bool(re_a))) if (le_a or re_a) else None

    lw = kp("left_wrist"); rw = kp("right_wrist")
    ls2 = kp("left_shoulder"); rs2 = kp("right_shoulder")
    wrists_high = (lw and ls2 and lw[1] < ls2[1]) or (rw and rs2 and rw[1] < rs2[1])

    lh = kp("left_hip"); rh = kp("right_hip")
    hip_y = (((lh[1] if lh else 0)+(rh[1] if rh else 0)) / max(1,int(bool(lh))+int(bool(rh)))) if (lh or rh) else 999
    sh_y  = (((ls2[1] if ls2 else 0)+(rs2[1] if rs2 else 0)) / max(1,int(bool(ls2))+int(bool(rs2)))) if (ls2 or rs2) else 0

    exercise = "Standing"
    if hip_y < sh_y:
        exercise = "Bench Press"
    elif avg_knee and avg_knee < 120:
        exercise = "Squat"
    elif avg_knee and 120 <= avg_knee < 155:
        exercise = "Lunge"
    elif spine_angle and spine_angle < 140 and avg_knee and avg_knee >= 140:
        exercise = "Deadlift"
    elif wrists_high and avg_elbow and avg_elbow < 130:
        exercise = "Overhead Press"
    elif avg_elbow and avg_elbow < 100 and not wrists_high:
        exercise = "Bicep Curl"

    if exercise == "Squat":
        analyze_squat(kp, angles, issues)
        if spine_angle and spine_angle < 145:
            issues.append({"name": "Excessive Forward Lean",
                           "severity": round(min(1.0,(145-spine_angle)/60),2),
                           "message": "Torso too far forward - lower back risk"})
    elif exercise == "Deadlift":    analyze_deadlift(kp, angles, issues, spine_angle)
    elif exercise == "Bench Press": analyze_bench(kp, angles, issues)
    elif exercise == "Lunge":       analyze_lunge(kp, angles, issues)
    elif exercise == "Bicep Curl":  analyze_curl(kp, angles, issues)
    elif exercise == "Overhead Press": analyze_ohp(kp, angles, issues, spine_angle)
    else:
        if spine_angle and spine_angle < 155:
            issues.append({"name": "Slouched Posture",
                           "severity": round(min(1.0,(155-spine_angle)/50),2),
                           "message": "Maintain neutral spine"})

    risk_score = int(min(100, max([i["severity"] for i in issues])*70 + len(issues)*10)) if issues else 0

    return {"issues": issues, "angles": angles, "risk_score": risk_score, "exercise_detected": exercise}

def draw_skeleton(frame, keypoints, risk_score):
    color = (0,230,100) if risk_score < 30 else (30,210,255) if risk_score < 65 else (0,60,255)
    for a, b in SKELETON:
        if a >= len(keypoints) or b >= len(keypoints): continue
        ka, kb = keypoints[a], keypoints[b]
        if float(ka[2]) > 0.2 and float(kb[2]) > 0.2:
            cv2.line(frame, (int(ka[0]),int(ka[1])), (int(kb[0]),int(kb[1])), color, 2, cv2.LINE_AA)
    for kp in keypoints:
        if float(kp[2]) > 0.2:
            cx, cy = int(kp[0]), int(kp[1])
            cv2.circle(frame, (cx,cy), 5, (255,255,255), -1, cv2.LINE_AA)
            cv2.circle(frame, (cx,cy), 5, color, 2, cv2.LINE_AA)
    return frame

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        await websocket.send_text(json.dumps({"error": "Camera not found or already in use"}))
        await websocket.close()
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    frame_idx     = 0
    last_analysis = {"issues": [], "angles": {}, "risk_score": 0, "exercise_detected": "Detecting..."}
    last_kp       = None

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1

            if YOLO_AVAILABLE and frame_idx % 2 == 0:
                results = model(frame, verbose=False, device=DEVICE, conf=0.25)
                if results and results[0].keypoints is not None:
                    kps = results[0].keypoints.data
                    if len(kps) > 0:
                        last_kp       = kps[0].cpu().numpy()
                        last_analysis = analyze_posture(last_kp)
                    else:
                        last_kp = None
                        last_analysis["exercise_detected"] = "No person detected"

            if last_kp is not None:
                frame = draw_skeleton(frame, last_kp, last_analysis["risk_score"])

            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            await websocket.send_text(json.dumps({
                "frame":    base64.b64encode(buf).decode("utf-8"),
                "analysis": last_analysis,
                "ts":       time.time(),
            }))
            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        cap.release()

@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)