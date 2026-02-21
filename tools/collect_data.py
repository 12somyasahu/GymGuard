import cv2
import csv
import time
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from pose.detector import run_inference

EXERCISES = [
    "Squat",
    "Deadlift", 
    "Bench Press",
    "Lunge",
    "Bicep Curl",
    "Overhead Press",
    "Standing",
]

OUTPUT_FILE = "data/keypoints.csv"

def normalize_keypoints(kps, frame_w, frame_h):
    """Normalize keypoints to 0-1 relative to frame size"""
    flat = []
    for kp in kps:
        flat.append(float(kp[0]) / frame_w)
        flat.append(float(kp[1]) / frame_h)
    return flat

def main():
    print("\n=== GymGuard Data Collector ===\n")
    print("Exercises available:")
    for i, ex in enumerate(EXERCISES):
        print(f"  {i+1}. {ex}")
    
    choice = int(input("\nPick exercise number: ")) - 1
    exercise = EXERCISES[choice]
    count = int(input(f"How many samples to collect for '{exercise}'? (recommend 300+): "))
    
    print(f"\nGet ready to perform: {exercise}")
    print("Press SPACE to start collecting, Q to quit early\n")

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    Path("data").mkdir(exist_ok=True)
    file_exists = Path(OUTPUT_FILE).exists()
    
    csvfile = open(OUTPUT_FILE, "a", newline="")
    writer = csv.writer(csvfile)
    
    # Write header only if file is new
    if not file_exists:
        header = []
        for i in range(17):
            header += [f"kp{i}_x", f"kp{i}_y"]
        header.append("label")
        writer.writerow(header)

    collecting = False
    collected  = 0
    frame_idx  = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        kps = run_inference(frame) if frame_idx % 2 == 0 else None

        # Draw UI
        status_color = (0, 255, 0) if collecting else (0, 165, 255)
        status_text  = f"COLLECTING: {collected}/{count}" if collecting else "PRESS SPACE TO START"
        cv2.putText(frame, status_text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
        cv2.putText(frame, f"Exercise: {exercise}", (10, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        if kps is not None:
            # Draw basic skeleton dots
            for kp in kps:
                if float(kp[2]) > 0.2:
                    cv2.circle(frame, (int(kp[0]), int(kp[1])), 4, (0, 230, 100), -1)

            if collecting:
                row = normalize_keypoints(kps, 640, 480)
                row.append(exercise)
                writer.writerow(row)
                collected += 1

                if collected >= count:
                    print(f"\nDone! Collected {count} samples for {exercise}")
                    break
        else:
            cv2.putText(frame, "NO PERSON DETECTED", (10, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.imshow("GymGuard - Data Collector", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            collecting = True
            print("Collecting...")
        elif key == ord('q'):
            break

    cap.release()
    csvfile.close()
    cv2.destroyAllWindows()
    print(f"\nSaved to {OUTPUT_FILE}")
    print(f"Total rows in file: {sum(1 for _ in open(OUTPUT_FILE)) - 1}")

if __name__ == "__main__":
    main()