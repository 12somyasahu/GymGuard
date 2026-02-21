import cv2
import base64
import asyncio
import json
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

from pose.detector import run_inference, YOLO_AVAILABLE
from pose.drawing import draw_skeleton
from pose.analyzers.base import analyze_posture

app = FastAPI(title="GymGuard")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        await websocket.send_text(json.dumps({"error": "Camera not found"}))
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

            if frame_idx % 2 == 0:
                kp = run_inference(frame)
                if kp is not None:
                    last_kp       = kp
                    last_analysis = analyze_posture(kp)
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
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)