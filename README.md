# 🏋️ GymGuard — Real-Time AI Injury Prediction

> GPU-powered posture analysis and injury risk scoring using your webcam, built with YOLOv8-Pose + FastAPI.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green?style=flat-square&logo=fastapi)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Pose-red?style=flat-square)
![CUDA](https://img.shields.io/badge/CUDA-12.x-76b900?style=flat-square&logo=nvidia)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## What It Does

GymGuard watches your workout through your webcam in real time, tracks 17 body keypoints using YOLOv8-Pose on your GPU, and scores your injury risk from 0–100 based on your joint angles and posture.

It detects bad form before it becomes an injury.

---

## Exercises Supported

| Exercise | What It Checks |
|---|---|
| Squat | Knee valgus, excessive forward lean |
| Deadlift | Spine rounding, bar drift |
| Bench Press | Elbow flare, wrist alignment |
| Lunge | Knee over toe, torso lean |
| Bicep Curl | Body swing / cheat reps |
| Overhead Press | Lumbar hyperextension |
| Standing | General posture, forward head |

---

## Risk Scoring

| Score | Level | Meaning |
|---|---|---|
| 0 – 29 | 🟢 SAFE | Good form |
| 30 – 64 | 🟡 WARNING | Deviations detected, reduce load |
| 65 – 100 | 🔴 HIGH RISK | Stop and correct immediately |

---

## Tech Stack

- **YOLOv8-Pose** (Ultralytics) — real-time 17-point body keypoint detection
- **PyTorch + CUDA** — GPU inference on NVIDIA GPUs
- **FastAPI + WebSockets** — streams processed frames to the browser
- **OpenCV** — webcam capture and skeleton drawing
- **Vanilla HTML/CSS/JS** — zero framework frontend with live canvas chart

---

## Requirements

- Python 3.10+
- NVIDIA GPU with CUDA support (tested on RTX 3050)
- Webcam

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/gymguard.git
cd gymguard
```

### 2. Create a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate
```

### 3. Install PyTorch with CUDA
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

Verify your GPU is detected:
```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
# Should print: True  NVIDIA GeForce RTX XXXX
```

### 4. Install remaining dependencies
```bash
pip install -r requirements.txt
```

### 5. Run
```bash
python main.py
```

Open your browser at **http://localhost:8000**

> ⚠️ Do NOT open `static/index.html` directly. Always go through `http://localhost:8000`.

On first run, YOLOv8 will automatically download `yolov8m-pose.pt` (~50MB).

---

## Project Structure
```
gymguard/
│
├── main.py                  # FastAPI backend + YOLOv8 inference
├── requirements.txt
├── .gitignore
├── README.md
│
├── static/
│   └── index.html           # Frontend dashboard
│
├── analyzers/               # Per-exercise analysis modules (WIP)
│   ├── squat.py
│   ├── deadlift.py
│   ├── bench.py
│   ├── lunge.py
│   ├── curl.py
│   └── overhead_press.py
│
├── models/                  # Custom trained models (future)
│   └── .gitkeep
│
└── data/                    # Training data (future)
    └── .gitkeep
```

---

## How It Works
```
Webcam (640x480 @ 30fps)
    |
    v
YOLOv8m-Pose (NVIDIA GPU / CUDA)
    |  17 body keypoints detected per frame
    v
Posture Analysis Engine
    |  Joint angles calculated (knee, spine, elbow, hip, neck)
    |  Exercise auto-detected from keypoint positions
    |  Rule-based issue detection per exercise
    v
Injury Risk Score (0-100)
    |
    v
FastAPI WebSocket --> Browser Dashboard
    |  Live video feed with skeleton overlay
    |  Real-time risk gauge
    |  Form issue alerts
    |  60-second scrolling history chart
    |  CSV export
```

---

## Performance

Tested on **NVIDIA GeForce RTX 3050 Laptop (6GB VRAM)**:

| Model | FPS | Accuracy |
|---|---|---|
| yolov8n-pose | ~28 FPS | Good |
| yolov8m-pose | ~20 FPS | Better |
| yolov8l-pose | ~12 FPS | Best |

To swap models, change this line in `main.py`:
```python
model = YOLO("yolov8m-pose.pt")  # change to yolov8n-pose.pt or yolov8l-pose.pt
```

---

## Roadmap

- [ ] Rep counter per exercise
- [ ] Voice alerts for bad form
- [ ] Session history page with past workout data
- [ ] Multi-person detection
- [ ] Mobile responsive layout
- [ ] Custom trained model on gym-specific dataset (not just COCO)
- [ ] Export session report as PDF

---

## Contributing

Pull requests are welcome. If you want to add a new exercise analyzer, create a file in `analyzers/` following the same pattern as the existing ones and wire it into `main.py`.

---

## License

MIT — do whatever you want with it.

---

## Author

Built by [Somya Sahu and Team](https://github.com/12somyasahu).  
If this helped you, give it a star ⭐