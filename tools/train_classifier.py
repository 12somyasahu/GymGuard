import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import json

DATA_FILE  = "data/keypoints.csv"
MODEL_FILE = "models/exercise_classifier.pkl"
LABEL_FILE = "models/label_encoder.pkl"

def train():
    print("Loading data...")
    df = pd.read_csv(DATA_FILE)
    print(f"Total samples: {len(df)}")
    print(f"Per exercise:\n{df['label'].value_counts()}\n")

    # Features = all keypoint columns
    feature_cols = [c for c in df.columns if c != "label"]
    X = df[feature_cols].values
    y = df["label"].values

    # Encode labels
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    print(f"Classes: {list(le.classes_)}\n")

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )

    print("Training classifier...")
    clf = MLPClassifier(
        hidden_layer_sizes=(128, 64),
        activation="relu",
        max_iter=500,
        random_state=42,
        verbose=True,
        early_stopping=True,
        validation_fraction=0.1,
    )
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    print("\n=== Results ===")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    print("Confusion Matrix:")
    print(pd.DataFrame(cm, index=le.classes_, columns=le.classes_))

    # Save
    Path("models").mkdir(exist_ok=True)
    joblib.dump(clf, MODEL_FILE)
    joblib.dump(le,  LABEL_FILE)
    print(f"\nModel saved to {MODEL_FILE}")
    print(f"Accuracy: {clf.score(X_test, y_test)*100:.1f}%")

if __name__ == "__main__":
    train()