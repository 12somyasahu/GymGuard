import cv2
import base64
import asyncio
import json
import time
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pathlib import Path
import tempfile
import os

from pose.detector import run_inference, YOLO_AVAILABLE
from pose.drawing import draw_skeleton
from pose.analyzers.base import analyze_posture

app = FastAPI(title="GymGuard")

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    contents  = await file.read()
    nparr     = np.frombuffer(contents, np.uint8)
    frame     = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    kp = run_inference(frame)
    if kp is not None:
        analysis = analyze_posture(kp)
        frame    = draw_skeleton(frame, kp, analysis["risk_score"])
    else:
        analysis = {"issues": [], "angles": {}, "risk_score": 0, "exercise_detected": "No person detected"}

    _, buf    = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    frame_b64 = base64.b64encode(buf).decode("utf-8")
    return {"frame": frame_b64, "analysis": analysis}


@app.post("/analyze-video")
async def analyze_video(file: UploadFile = File(...)):
    # Save uploaded video to temp file
    suffix = Path(file.filename).suffix or ".mp4"
    tmp    = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(await file.read())
    tmp.close()

    def generate():
        cap = cv2.VideoCapture(tmp.name)
        frame_idx = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx += 1
                if frame_idx % 3 != 0:   # process every 3rd frame
                    continue

                kp = run_inference(frame)
                if kp is not None:
                    analysis = analyze_posture(kp)
                    frame    = draw_skeleton(frame, kp, analysis["risk_score"])
                else:
                    analysis = {"issues": [], "angles": {}, "risk_score": 0, "exercise_detected": "No person detected"}

                _, buf    = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                frame_b64 = base64.b64encode(buf).decode("utf-8")

                payload = json.dumps({"frame": frame_b64, "analysis": analysis}) + "\n"
                yield payload.encode("utf-8")

        finally:
            cap.release()
            os.unlink(tmp.name)

    return StreamingResponse(generate(), media_type="application/x-ndjson")


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