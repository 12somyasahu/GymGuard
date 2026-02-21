import cv2
import csv
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from pose.detector import run_inference

VIDEO_DIR  = Path("data/videos")
OUTPUT_CSV = Path("data/keypoints.csv")

# Sample every Nth frame — no need for every single frame
# 10 = extract one frame every 10 frames (reduces duplicates)
FRAME_SKIP = 10

EXERCISES = ["squat", "deadlift", "bench", "lunge", "curl", "overhead", "standing"]

# Map folder name to label name
LABEL_MAP = {
    "squat":    "Squat",
    "deadlift": "Deadlift",
    "bench":    "Bench Press",
    "lunge":    "Lunge",
    "curl":     "Bicep Curl",
    "overhead": "Overhead Press",
    "standing": "Standing",
}

def normalize_keypoints(kps, frame_w, frame_h):
    flat = []
    for kp in kps:
        flat.append(float(kp[0]) / frame_w)
        flat.append(float(kp[1]) / frame_h)
    return flat

def process_video(video_path, label, writer):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"  Could not open {video_path.name}")
        return 0

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    saved = 0
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1

        # Skip frames to avoid near-duplicate samples
        if frame_idx % FRAME_SKIP != 0:
            continue

        kps = run_inference(frame)

        if kps is not None:
            row = normalize_keypoints(kps, frame_w, frame_h)
            row.append(label)
            writer.writerow(row)
            saved += 1

        # Progress
        if frame_idx % 100 == 0:
            pct = (frame_idx / total_frames) * 100 if total_frames > 0 else 0
            print(f"  {video_path.name}: {pct:.0f}% ({saved} samples so far)")

    cap.release()
    return saved

def main():
    print("=== GymGuard Video Keypoint Extractor ===\n")

    # Write CSV header
    OUTPUT_CSV.parent.mkdir(exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        header = []
        for i in range(17):
            header += [f"kp{i}_x", f"kp{i}_y"]
        header.append("label")
        writer.writerow(header)

    total_saved = 0

    # Process each exercise folder
    with open(OUTPUT_CSV, "a", newline="") as f:
        writer = csv.writer(f)

        for exercise_folder in EXERCISES:
            folder = VIDEO_DIR / exercise_folder
            label  = LABEL_MAP[exercise_folder]

            if not folder.exists():
                print(f"Skipping {exercise_folder} - folder not found")
                continue

            videos = list(folder.glob("*.mp4")) + list(folder.glob("*.webm"))
            if not videos:
                print(f"Skipping {exercise_folder} - no videos found")
                continue

            print(f"\nProcessing: {label} ({len(videos)} videos)")

            exercise_total = 0
            for video in videos:
                print(f"  -> {video.name}")
                saved = process_video(video, label, writer)
                exercise_total += saved
                print(f"     Saved {saved} samples")

            print(f"  Total for {label}: {exercise_total} samples")
            total_saved += exercise_total

    print(f"\nDone! Total samples saved: {total_saved}")
    print(f"CSV saved to: {OUTPUT_CSV}")
    print(f"\nNow run: python tools/train_classifier.py")

if __name__ == "__main__":
    main()