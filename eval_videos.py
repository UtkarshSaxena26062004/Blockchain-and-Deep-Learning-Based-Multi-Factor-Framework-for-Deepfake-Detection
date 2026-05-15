# eval_videos.py
import os, json, math
import numpy as np
import pandas as pd
import cv2
from tensorflow.keras.models import load_model
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt, itertools

# ---------- CONFIG ----------
MODEL_PATH = os.path.join("model", "deepfake_model.h5")
TEST_ROOT = "SDFVD/test"    # directory with subfolders per class containing videos
REPORT_DIR = "reports"
TARGET_SIZE = (299, 299)    # model input size
FRAME_STEP = 10             # sample every N-th frame (adjust: 5-30)
BATCH_FRAMES = 32           # frames per predict batch to speed up
# ----------------------------

os.makedirs(REPORT_DIR, exist_ok=True)
print("Loading model:", MODEL_PATH)
model = load_model(MODEL_PATH)
print("Model loaded.")

# find classes from subfolders under TEST_ROOT
classes = sorted([d for d in os.listdir(TEST_ROOT) if os.path.isdir(os.path.join(TEST_ROOT, d))])
if not classes:
    raise SystemExit(f"No class subfolders found under {TEST_ROOT}. Make sure structure is {TEST_ROOT}/<class>/*.mp4")

print("Detected classes:", classes)
y_true_list = []
y_pred_list = []
video_names = []

def predict_frames_batch(frames):
    """
    frames: list of numpy arrays (H,W,3) already resized to TARGET_SIZE and scaled [0,1]
    returns: numpy array of model outputs shape (N, ...) 
    """
    arr = np.stack(frames, axis=0)
    preds = model.predict(arr, batch_size=arr.shape[0], verbose=0)
    return preds

# iterate classes and videos
for label_idx, cls in enumerate(classes):
    cls_dir = os.path.join(TEST_ROOT, cls)
    for fname in sorted(os.listdir(cls_dir)):
        if not fname.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            continue
        video_path = os.path.join(cls_dir, fname)
        print(f"Processing [{cls}] {fname} ...")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("  ⚠️ Cannot open video:", video_path)
            continue

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        sampled_frames = []
        frame_idx = 0
        frames_for_batch = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % FRAME_STEP == 0:
                # convert BGR->RGB, resize, scale
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                resized = cv2.resize(rgb, TARGET_SIZE)
                resized = resized.astype("float32") / 255.0
                frames_for_batch.append(resized)
                # if batch ready, predict and collect
                if len(frames_for_batch) >= BATCH_FRAMES:
                    preds = predict_frames_batch(frames_for_batch)
                    for p in preds:
                        # if binary output is single neuron, p could be scalar or array
                        sampled_frames.append(p)
                    frames_for_batch = []
            frame_idx += 1

        # leftover batch
        if frames_for_batch:
            preds = predict_frames_batch(frames_for_batch)
            for p in preds:
                sampled_frames.append(p)
            frames_for_batch = []

        cap.release()

        if not sampled_frames:
            print("  ⚠️ No frames sampled for", fname)
            continue

        # convert list of preds to numpy
        sampled_preds = np.array(sampled_frames)
        # handle shape:
        # case A: binary output with shape (N,1) or (N,) -> reduce to scalar per frame
        if sampled_preds.ndim == 2 and sampled_preds.shape[1] == 1:
            sampled_preds = sampled_preds.ravel()
        # case B: multiclass raw logits/probs shape (N, C) -> take argmax per frame
        # Now compute video-level decision:
        if sampled_preds.ndim == 1:
            # binary: average probability; threshold 0.5
            video_score = float(np.mean(sampled_preds))  # probability of class 1 (depends on training)
            video_pred = int(video_score >= 0.5)
        else:
            # multiclass: average predicted probabilities then argmax
            mean_prob = np.mean(sampled_preds, axis=0)
            video_pred = int(np.argmax(mean_prob))
            video_score = float(np.max(mean_prob))

        y_true_list.append(label_idx)
        y_pred_list.append(video_pred)
        video_names.append(f"{cls}/{fname}")

        print(f"  frames_sampled={len(sampled_preds)} video_score={video_score:.4f} pred={video_pred}")

# convert and evaluate
y_true = np.array(y_true_list, dtype=int)
y_pred = np.array(y_pred_list, dtype=int)

if len(y_true) == 0:
    raise SystemExit("No videos processed. Check TEST_ROOT and video files.")

# classification report & confusion matrix
report_dict = classification_report(y_true, y_pred, target_names=classes, output_dict=True, digits=4)
report_csv = os.path.join(REPORT_DIR, "classification_report.csv")
pd.DataFrame(report_dict).transpose().to_csv(report_csv)
with open(os.path.join(REPORT_DIR, "classification_report.json"), "w") as f:
    json.dump(report_dict, f, indent=2)

np.save(os.path.join(REPORT_DIR, "y_true.npy"), y_true)
np.save(os.path.join(REPORT_DIR, "y_pred.npy"), y_pred)
with open(os.path.join(REPORT_DIR, "classes.json"), "w") as f:
    json.dump(classes, f)

cm = confusion_matrix(y_true, y_pred)
print("\nClassification report saved to:", report_csv)
print("Confusion matrix:\n", cm)

# plot & save confusion matrices
def plot_and_save_cm(cm, classes, out_path, normalize=False):
    if normalize:
        with np.errstate(all='ignore'):
            cm_disp = cm.astype('float') / cm.sum(axis=1)[:, None]
            cm_disp = np.nan_to_num(cm_disp)
    else:
        cm_disp = cm

    fig, ax = plt.subplots(figsize=(8,6))
    im = ax.imshow(cm_disp, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    ax.set(xticks=np.arange(len(classes)),
           yticks=np.arange(len(classes)),
           xticklabels=classes, yticklabels=classes,
           ylabel='True label', xlabel='Predicted label')
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    thresh = cm_disp.max()/2. if cm_disp.max() != 0 else 0.5
    for i, j in itertools.product(range(cm_disp.shape[0]), range(cm_disp.shape[1])):
        val = cm_disp[i,j]
        txt = f"{val:.2f}" if normalize else f"{int(val)}"
        ax.text(j, i, txt, ha='center', va='center', color='white' if val>thresh else 'black', fontsize=10)
    plt.tight_layout()
    fig.savefig(out_path, bbox_inches='tight', dpi=150)
    plt.close(fig)
    print("Saved:", out_path)

plot_and_save_cm(cm, classes, os.path.join(REPORT_DIR, "confusion_counts.png"), normalize=False)
plot_and_save_cm(cm, classes, os.path.join(REPORT_DIR, "confusion_norm.png"), normalize=True)

print("✅ All reports saved in", REPORT_DIR)
