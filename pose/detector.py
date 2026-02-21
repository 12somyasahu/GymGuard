import numpy as np

try:
    from ultralytics import YOLO
    import torch

    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[INFO] Using device: {DEVICE}")

    model = YOLO("yolov8m-pose.pt")

    dummy = np.zeros((480, 640, 3), dtype=np.uint8)
    model(dummy, verbose=False, device=DEVICE)
    print("[INFO] GPU warm-up complete")

    YOLO_AVAILABLE = True
    print("[INFO] YOLOv8m-Pose ready")

except Exception as e:
    print(f"[WARN] YOLOv8 not available: {e}")
    YOLO_AVAILABLE = False
    DEVICE = "cpu"
    model = None


def run_inference(frame):
    """
    Returns numpy keypoints array for first detected person, or None.
    """
    if not YOLO_AVAILABLE:
        return None

    results = model(frame, verbose=False, device=DEVICE, conf=0.25)

    if results and results[0].keypoints is not None:
        kps = results[0].keypoints.data
        if len(kps) > 0:
            return kps[0].cpu().numpy()

    return None