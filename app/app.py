import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import io
import base64
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report
import pandas as pd
import itertools
from markupsafe import Markup

from app.blockchain.contract_client import ContractClient
import json
import datetime
import numpy as np
import cv2
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from fpdf import FPDF
from app.utils.hash_utils import sha256_of_file
import csv
from pathlib import Path
import platform
import tensorflow as tf

# ========== CONFIG ==========
UPLOAD_FOLDER = 'uploads'
REPORT_FOLDER = 'reports'
MODEL_PATH = 'model/deepfake_model.h5'
THUMBS_FOLDER = os.path.join(REPORT_FOLDER, 'thumbs')
UPLOADS_PRED_CSV = os.path.join(REPORT_FOLDER, "uploads_preds.csv")
FRAME_STEP_DEFAULT = 10
BATCH_FRAMES_DEFAULT = 32
TARGET_SIZE = (299, 299)
# ============================

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)
os.makedirs(THUMBS_FOLDER, exist_ok=True)

# create uploads CSV header if missing
Path(REPORT_FOLDER).mkdir(parents=True, exist_ok=True)
if not os.path.exists(UPLOADS_PRED_CSV):
    with open(UPLOADS_PRED_CSV, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "filename", "predicted_label", "score", "report_json"])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "dev-secret"

# === Load model ===
# print("🔹 Loading model, please wait...")
# model = load_model(MODEL_PATH, compile=False)
# print("✅ Model loaded successfully!")
import tensorflow as tf

print("🔹 Loading model, please wait...")

from tensorflow.keras.applications import Xception
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Model

# Build same architecture used during training
base_model = Xception(
    weights=None,
    include_top=False,
    input_shape=(299, 299, 3)
)

x = base_model.output
x = GlobalAveragePooling2D(name="avg_pool")(x)
predictions = Dense(1, activation="sigmoid", name="predictions")(x)

model = Model(inputs=base_model.input, outputs=predictions)

# 🔥 Important: load weights by name and skip mismatch layers
model.load_weights(
    MODEL_PATH,
    by_name=True,
    skip_mismatch=True
)

print("✅ Model loaded successfully!")

# === Load blockchain client (best-effort) ===
try:
    blockchain_client = ContractClient()
    print("✅ Connected to Blockchain at:", blockchain_client.address)
except Exception as e:
    print("⚠️ Blockchain connection failed:", e)
    blockchain_client = None

# === Helper Functions ===
def predict_image_single(img_path):
    """Return (score, frame_scores=[], thumbs[]) for image file."""
    try:
        img = image.load_img(img_path, target_size=TARGET_SIZE)
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0) / 255.0
        pred = model.predict(img_array)[0]
        # normalize to scalar
        if np.ndim(pred) == 0:
            score = float(pred)
        elif np.ndim(pred) == 1 and pred.shape[0] == 1:
            score = float(pred[0])
        else:
            score = float(np.max(pred))
        # save a thumbnail (copy image into reports/thumbs)
        thumb_name = f"thumb_{os.path.splitext(os.path.basename(img_path))[0]}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        thumb_path = os.path.join(THUMBS_FOLDER, thumb_name)
        cv_img = cv2.imread(img_path)
        if cv_img is not None:
            cv2.imwrite(thumb_path, cv_img)
            thumb_rel = os.path.join('thumbs', thumb_name)  # relative to reports/
        else:
            thumb_rel = None
        return score, [], [thumb_rel] if thumb_rel else []
    except Exception as e:
        print("⚠️ Error in image prediction:", e)
        return 0.5, [], []

def predict_video_with_frames(video_path, every_n=FRAME_STEP_DEFAULT, batch_frames=BATCH_FRAMES_DEFAULT, max_thumbs=5):
    """
    Return (video_score, frame_scores_list, thumbs_rel_paths)
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("⚠️ Cannot open video:", video_path)
        return 0.5, [], []

    sampled_preds = []
    frames_batch = []
    frame_idx = 0
    thumbs = []
    saved_thumb_count = 0

    def predict_batch(frames):
        arr = np.stack(frames, axis=0)
        preds = model.predict(arr, batch_size=arr.shape[0], verbose=0)
        return preds

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % every_n == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resized = cv2.resize(rgb, TARGET_SIZE)
            resized = resized.astype("float32") / 255.0
            frames_batch.append(resized)
            # save some thumbs (BGR copy)
            if saved_thumb_count < max_thumbs:
                thumb_name = f"{os.path.splitext(os.path.basename(video_path))[0]}_frame{frame_idx}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                thumb_path = os.path.join(THUMBS_FOLDER, thumb_name)
                cv2.imwrite(thumb_path, frame)  # save original BGR
                thumbs.append(os.path.join('thumbs', thumb_name))  # relative to reports/
                saved_thumb_count += 1
            if len(frames_batch) >= batch_frames:
                preds = predict_batch(frames_batch)
                for p in preds:
                    sampled_preds.append(p)
                frames_batch = []
        frame_idx += 1

    # leftover
    if frames_batch:
        preds = predict_batch(frames_batch)
        for p in preds:
            sampled_preds.append(p)
        frames_batch = []

    cap.release()

    if len(sampled_preds) == 0:
        return 0.5, [], thumbs

    sampled_preds = np.array(sampled_preds)
    if sampled_preds.ndim == 2 and sampled_preds.shape[1] == 1:
        sampled_preds = sampled_preds.ravel()

    if sampled_preds.ndim == 1:
        video_score = float(np.mean(sampled_preds))
        frame_scores = [float(x) for x in sampled_preds.tolist()]
    else:
        mean_prob = np.mean(sampled_preds, axis=0)
        video_score = float(np.max(mean_prob))
        frame_scores = [float(np.max(p)) for p in sampled_preds.tolist()]

    return video_score, frame_scores, thumbs

def sha256_of_file_wrapper(path):
    try:
        return sha256_of_file(path)
    except Exception:
        return None

# Robust Grad-CAM generator (safe)
def generate_heatmap(img_path):
    import tensorflow as tf
    try:
        img = tf.keras.preprocessing.image.load_img(img_path, target_size=TARGET_SIZE)
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0) / 255.0
    except Exception as e:
        raise RuntimeError("Failed to load image for heatmap: " + str(e))

    # find last conv layer
    last_conv_layer = None
    for layer in reversed(model.layers):
        try:
            if hasattr(layer.output_shape, '__len__') and len(layer.output_shape) == 4:
                last_conv_layer = layer.name
                break
        except Exception:
            continue

    if last_conv_layer is None:
        raise RuntimeError("No convolutional layer found for Grad-CAM.")

    grad_model = tf.keras.models.Model([model.inputs], [model.get_layer(last_conv_layer).output, model.output])

    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_array)
        if predictions.ndim == 2 and predictions.shape[1] == 1:
            loss = predictions[:, 0]
        else:
            pred_index = tf.argmax(predictions[0])
            loss = predictions[:, pred_index]

    grads = tape.gradient(loss, conv_outputs)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_outputs = conv_outputs[0]
    heatmap = tf.reduce_mean(tf.multiply(pooled_grads, conv_outputs), axis=-1)
    heatmap = np.maximum(heatmap, 0)
    if np.max(heatmap) != 0:
        heatmap /= np.max(heatmap)
    heatmap = cv2.resize(heatmap.numpy(), TARGET_SIZE)
    heatmap = np.uint8(255 * heatmap)
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

    original = cv2.imread(img_path)
    if original is None:
        raise RuntimeError("Original image could not be read for heatmap.")
    original = cv2.resize(original, TARGET_SIZE)
    superimposed_img = cv2.addWeighted(original, 0.6, heatmap, 0.4, 0)
    os.makedirs("static/heatmaps", exist_ok=True)
    output_path = os.path.join("static/heatmaps", os.path.basename(img_path))
    cv2.imwrite(output_path, superimposed_img)
    return output_path

# ---------- Helpers for metrics & plots ----------
def plot_cm_to_base64(cm, classes, normalize=False, title="Confusion Matrix", figsize=(8,6)):
    if normalize:
        with np.errstate(all='ignore'):
            cm_display = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
            cm_display = np.nan_to_num(cm_display)
    else:
        cm_display = cm

    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(cm_display, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    ax.set(xticks=np.arange(len(classes)),
           yticks=np.arange(len(classes)),
           xticklabels=classes, yticklabels=classes,
           ylabel='True label',
           xlabel='Predicted label',
           title=title)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    thresh = cm_display.max() / 2. if cm_display.max() != 0 else 0.5
    for i, j in itertools.product(range(cm_display.shape[0]), range(cm_display.shape[1])):
        val = cm_display[i, j]
        text = f"{val:.2f}" if normalize else f"{int(val)}"
        ax.text(j, i, text, ha="center", va="center",
                color="white" if val > thresh else "black", fontsize=10)

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def _save_reports_and_assets(y_true, y_pred, classes):
    report_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
    if not os.path.isdir(report_dir):
        report_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(report_dir, exist_ok=True)

    cm = confusion_matrix(y_true, y_pred)
    cm_path = os.path.join(report_dir, "confusion_counts.png")
    cm_norm_path = os.path.join(report_dir, "confusion_norm.png")

    png_counts_b64 = plot_cm_to_base64(cm, classes, normalize=False, title="Confusion Matrix (counts)")
    with open(cm_path, "wb") as f:
        f.write(base64.b64decode(png_counts_b64))
    png_norm_b64 = plot_cm_to_base64(cm, classes, normalize=True, title="Confusion Matrix (normalized)")
    with open(cm_norm_path, "wb") as f:
        f.write(base64.b64decode(png_norm_b64))

    rep = classification_report(y_true, y_pred, target_names=classes, output_dict=True, digits=4)
    rep_csv = os.path.join(report_dir, "classification_report.csv")
    rep_json = os.path.join(report_dir, "classification_report.json")
    pd.DataFrame(rep).transpose().to_csv(rep_csv)
    with open(rep_json, "w") as f:
        json.dump(rep, f, indent=2)

    np.save(os.path.join(report_dir, "y_true.npy"), y_true)
    np.save(os.path.join(report_dir, "y_pred.npy"), y_pred)
    with open(os.path.join(report_dir, "classes.json"), "w") as f:
        json.dump(classes, f)

    print("✅ Saved reports to:", report_dir)

def compute_metrics_from_videos(test_root, target_size=(299,299), frame_step=10, batch_frames=32):
    classes = sorted([d for d in os.listdir(test_root) if os.path.isdir(os.path.join(test_root, d))])
    if not classes:
        raise RuntimeError(f"No class subfolders under {test_root}")

    y_true_list = []
    y_pred_list = []

    def predict_frames_batch(frames):
        arr = np.stack(frames, axis=0)
        preds = model.predict(arr, batch_size=arr.shape[0], verbose=0)
        return preds

    for label_idx, cls in enumerate(classes):
        cls_dir = os.path.join(test_root, cls)
        for fname in sorted(os.listdir(cls_dir)):
            if not fname.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                continue
            video_path = os.path.join(cls_dir, fname)
            print(f"Processing video [{cls}] {fname} ...")
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print("  ⚠️ Cannot open video:", video_path)
                continue

            sampled_preds = []
            frames_batch = []
            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_idx % frame_step == 0:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    resized = cv2.resize(rgb, target_size)
                    resized = resized.astype("float32") / 255.0
                    frames_batch.append(resized)
                    if len(frames_batch) >= batch_frames:
                        preds = predict_frames_batch(frames_batch)
                        for p in preds:
                            sampled_preds.append(p)
                        frames_batch = []
                frame_idx += 1

            if frames_batch:
                preds = predict_frames_batch(frames_batch)
                for p in preds:
                    sampled_preds.append(p)
                frames_batch = []

            cap.release()

            if len(sampled_preds) == 0:
                print("  ⚠️ No frames sampled for", fname)
                continue

            sampled_preds = np.array(sampled_preds)
            if sampled_preds.ndim == 2 and sampled_preds.shape[1] == 1:
                sampled_preds = sampled_preds.ravel()
            if sampled_preds.ndim == 1:
                video_score = float(np.mean(sampled_preds))
                video_pred = int(video_score >= 0.5)
            else:
                mean_prob = np.mean(sampled_preds, axis=0)
                video_pred = int(np.argmax(mean_prob))

            y_true_list.append(label_idx)
            y_pred_list.append(video_pred)
            print(f"  frames={len(sampled_preds)} video_pred={video_pred}")

    y_true = np.array(y_true_list, dtype=int)
    y_pred = np.array(y_pred_list, dtype=int)
    _save_reports_and_assets(y_true, y_pred, classes)
    return y_true, y_pred, classes
def get_ground_truth_for(filename):
    """
    ground_truths.csv se given filename ka last (latest) true label nikalta hai.
    Format: [timestamp, filename, label]
    """
    gt_csv = os.path.join(REPORT_FOLDER, 'ground_truths.csv')
    if not os.path.exists(gt_csv):
        return None

    last = None
    with open(gt_csv, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3 and row[1] == filename:
                last = row[2]   # latest wali overwrite hoti rahegi
    return last


# === Routes ===
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    f = request.files.get('file')
    if not f or f.filename.strip() == '':
        flash("No file selected")
        return redirect(url_for('index'))

    filename = f.filename.replace(' ', '_')
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    f.save(path)

    ext = os.path.splitext(filename)[1].lower()
    if ext in ['.jpg', '.jpeg', '.png']:
        score, frame_scores, thumbs = predict_image_single(path)
    elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
        score, frame_scores, thumbs = predict_video_with_frames(
            path,
            every_n=FRAME_STEP_DEFAULT,
            batch_frames=BATCH_FRAMES_DEFAULT,
            max_thumbs=5
        )
    else:
        return "❌ Unsupported file type."

    # ------------ blockchain part same rakha ------------
    hexhash = sha256_of_file_wrapper(path)
    bc_verified = False
    tx_hash = None
    if blockchain_client:
        try:
            already = blockchain_client.verify_hash(hexhash)
            if already:
                bc_verified = True
            elif score < 0.5:
                receipt = blockchain_client.store_hash(hexhash)
                bc_verified = True
                tx_hash = getattr(receipt, 'transactionHash', None)
        except Exception as e:
            print("⚠️ Blockchain Error:", e)
            bc_verified = False
    # -----------------------------------------------------

    metadata_score = 0.8
    authenticity = round(
        (0.6 * (1 - score)) +
        (0.3 * metadata_score) +
        (0.1 * int(bc_verified)),
        3
    )

    # ---- NEW: model prediction + feedback-based final label ----
    predicted_label = "fake" if score >= 0.5 else "real"

    # agar is filename ke liye pehle se feedback diya gaya hai, to woh le aao
    true_label = get_ground_truth_for(filename)
    # final label: feedback ko priority, warna model prediction
    final_label = true_label if true_label is not None else predicted_label
    # ------------------------------------------------------------

    report = {
    'file': filename,
    'ai_score': round(score, 4),
    'frame_scores': frame_scores,
    'thumbs': thumbs,
    'blockchain_verified': bc_verified,
    'tx_hash': tx_hash.hex() if tx_hash is not None and hasattr(tx_hash, "hex") else (tx_hash or None),
    'authenticity_score': authenticity,
    'hash': hexhash,
    'model_name': os.path.basename(MODEL_PATH),
    'model_sha256': sha256_of_file_wrapper(MODEL_PATH),
    'tf_version': tf.__version__,
    'python_version': platform.python_version(),
    'generated_at': datetime.datetime.now().isoformat(),

    # 🔥 VERY IMPORTANT
    'predicted_label': predicted_label,
    'true_label': true_label,
    'final_label': final_label,
}


    # save JSON in reports/
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f'report_{ts}.json'
    report_path = os.path.join(REPORT_FOLDER, report_filename)
    with open(report_path, 'w', encoding='utf-8') as rf:
        json.dump(report, rf, indent=2)

    # append to uploads CSV index
    # ⚠ CSV ka structure purana hi rakha hai taaki uploads.html na toot jaaye
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(UPLOADS_PRED_CSV, "a", newline='', encoding='utf-8') as fcsv:
        writer = csv.writer(fcsv)
        writer.writerow([
            timestamp_str,
            filename,
            predicted_label,                    # same as pehle
            round(float(score), 4),
            report_filename
        ])

    return render_template('result.html', report=report)


@app.route('/uploads')
def uploads_page():
    rows = []
    if os.path.exists(UPLOADS_PRED_CSV):
        with open(UPLOADS_PRED_CSV, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)[::-1]  # newest first
    fake_count = sum(1 for r in rows if r["predicted_label"] == "fake")
    real_count = sum(1 for r in rows if r["predicted_label"] == "real")
    return render_template("uploads.html", rows=rows, fake_count=fake_count, real_count=real_count)

@app.route('/reports/download/<path:filename>')
def download_report_file(filename):
    report_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
    if not os.path.isdir(report_dir):
        report_dir = os.path.join(os.getcwd(), "reports")
    path = os.path.join(report_dir, filename)
    if not os.path.exists(path):
        return "File not found", 404
    return send_file(path)

@app.route('/uploads/raw/<path:filename>')
def uploaded_file(filename):
    # Ensure file is served from uploads/raw
    raw_folder = os.path.join(UPLOAD_FOLDER, "raw")
    path = os.path.join(raw_folder, filename)

    if not os.path.exists(path):
        return f"File not found: {path}", 404

    return send_file(path)


@app.route('/mark_truth/<filename>', methods=['POST'])
def mark_truth(filename):
    true_label = request.form.get('true_label')
    print("DEBUG mark_truth:", filename, true_label)  # optional

    if not true_label:
        return redirect(url_for('detailed_report', filename=filename))

    gt_csv = os.path.join(REPORT_FOLDER, 'ground_truths.csv')
    with open(gt_csv, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.datetime.now().isoformat(), filename, true_label])

    flash("Ground truth saved.")
    return redirect(url_for('detailed_report', filename=filename))


@app.route('/report_pdf/<filename>')
def report_pdf(filename):
    report_path = os.path.join(REPORT_FOLDER, filename)
    if not os.path.exists(report_path):
        return "Not found", 404

    with open(report_path, "r", encoding='utf-8') as f:
        report = json.load(f)

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('DejaVu', '', os.path.join(os.path.dirname(__file__), 'DejaVuSans.ttf'), uni=True)
    pdf.set_font("DejaVu", size=12)

    pdf.cell(0, 10, f"Detailed Report - {filename}", ln=True)
    pdf.ln(4)
    pdf.cell(0, 8, f"File: {report.get('file')}", ln=True)
    pdf.cell(0, 8, f"AI score: {report.get('ai_score')}", ln=True)
    pdf.cell(0, 8, f"Authenticity: {report.get('authenticity_score')}", ln=True)
    pdf.ln(6)

    if report.get('thumbs'):
        for t in report['thumbs'][:6]:
            p = os.path.join(REPORT_FOLDER, t) if not os.path.isabs(t) else t
            if os.path.exists(p):
                pdf.image(p, w=60)

    pdf.ln(6)
    pdf.multi_cell(0, 6, json.dumps(report, indent=2))

    # ✅ ABSOLUTE PATH USING app.root_path
    out_dir = os.path.join(app.root_path, 'static', 'reports')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename.replace('.json', '.pdf'))

    pdf.output(out_path)

    return send_file(out_path, as_attachment=True)


@app.route('/metrics')
def metrics():
    project_root = os.path.dirname(os.path.dirname(__file__))
    report_dir = os.path.join(project_root, "reports")
    if not os.path.isdir(report_dir):
        report_dir = os.path.join(os.getcwd(), "reports")
    cm_counts_path = os.path.join(report_dir, "confusion_counts.png")
    cm_norm_path = os.path.join(report_dir, "confusion_norm.png")
    report_csv_path = os.path.join(report_dir, "classification_report.csv")
    classes_json = os.path.join(report_dir, "classes.json")
    if not (os.path.exists(cm_counts_path) and os.path.exists(cm_norm_path) and os.path.exists(report_csv_path) and os.path.exists(classes_json)):
        sdfvd_test = os.path.join(project_root, "SDFVD", "test")
        data_test = os.path.join(project_root, "data", "test")
        if os.path.isdir(sdfvd_test):
            y_true, y_pred, classes = compute_metrics_from_videos(sdfvd_test, target_size=(299,299), frame_step=10, batch_frames=32)
        elif os.path.isdir(data_test):
            return ("<h3>Image-based compute not implemented in this build. Put video test set under SDFVD/test or precompute reports.</h3>")
        else:
            return ("<h3>No precomputed metrics found and no test dataset available at "
                    f"<code>{data_test}</code> or <code>{sdfvd_test}</code>. Put test images in <code>data/test/&lt;class&gt;/</code> or test videos in <code>SDFVD/test/&lt;class&gt;/</code>, or precompute reports.</h3>")
    else:
        with open(classes_json, "r") as f:
            classes = json.load(f)
    def _b64(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    img_counts_b64 = _b64(cm_counts_path)
    img_norm_b64 = _b64(cm_norm_path)
    df = pd.read_csv(report_csv_path, index_col=0)
    report_html = df.to_html(classes="table table-sm table-bordered", float_format="%.4f")
    return render_template("metrics.html",
                           cm_img_counts=img_counts_b64,
                           cm_img_norm=img_norm_b64,
                           report_table=Markup(report_html))

@app.route('/detailed_report/<filename>')
def detailed_report(filename):
    """
    Find the most-recent per-upload report JSON in REPORT_FOLDER whose "file" == filename.
    Skip any JSONs that are not dicts (e.g., classification_report.json which may be a list/dict of metrics).
    """
    report_files = []
    try:
        all_files = [f for f in os.listdir(REPORT_FOLDER) if f.endswith('.json')]
    except Exception:
        return f"<h3>Could not read reports folder: {REPORT_FOLDER}</h3>"

    # collect candidates with full path and mtime (to pick newest)
    for fname in all_files:
        full = os.path.join(REPORT_FOLDER, fname)
        try:
            mtime = os.path.getmtime(full)
        except Exception:
            mtime = 0
        report_files.append((full, mtime))

    # sort newest first
    report_files.sort(key=lambda x: x[1], reverse=True)

    target = None
    report_file_name = None

    for fullpath, _ in report_files:
        try:
            with open(fullpath, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception as e:
            # skip unreadable / invalid json files
            print(f"⚠️ Skipping {fullpath} (cannot load JSON): {e}")
            continue

        # only consider dict-shaped JSONs that look like per-upload reports
        if isinstance(data, dict) and data.get("file") == filename:
            target = data
            report_file_name = os.path.basename(fullpath)
            break
        else:
            # skip lists or other report-like JSONs
            continue

    if not target:
        return f"<h3>No per-upload report JSON found for <code>{filename}</code> in {REPORT_FOLDER}.</h3>"

    # ---------- NEW PART: read latest ground truth for this file ----------
    gt_csv = os.path.join(REPORT_FOLDER, 'ground_truths.csv')
    ground_truth = None
    if os.path.exists(gt_csv):
        with open(gt_csv, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                # row: [timestamp, filename, label]
                if len(row) >= 3 and row[1] == filename:
                    ground_truth = row[2]      # keep last match as "latest"
    # ---------------------------------------------------------------------

    file_path = os.path.join(UPLOAD_FOLDER, filename)
    heatmap_path = None
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        try:
            heatmap_path = generate_heatmap(file_path)
        except Exception as e:
            print("⚠️ Heatmap error:", e)
            heatmap_path = None

    return render_template(
        "detailed_report.html",
        report=target,
        heatmap=heatmap_path,
        filename=filename,
        report_file_name=report_file_name,
        ground_truth=ground_truth,      # <-- yahi missing tha upar
    )

import mimetypes
from flask import abort

@app.route('/reports/raw/<path:filename>')
def report_raw(filename):
    """
    Serve files that live inside the reports/ folder (like thumbs/... or confusion images)
    Inline (not as attachment) with correct MIME type so <img src=> will display them.
    Example URL used by template: url_for('report_raw', filename='thumbs/xxx.jpg')
    """
    report_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
    if not os.path.isdir(report_dir):
        report_dir = os.path.join(os.getcwd(), "reports")
    safe_path = os.path.normpath(os.path.join(report_dir, filename))

    # ensure requested file stays inside reports/ (prevent path traversal)
    if not safe_path.startswith(os.path.abspath(report_dir)):
        return abort(403)

    if not os.path.exists(safe_path):
        return abort(404)

    mime, _ = mimetypes.guess_type(safe_path)
    if mime is None:
        mime = "application/octet-stream"
    return send_file(safe_path, mimetype=mime)


@app.route('/dashboard')
def dashboard():
    """
    Build lists expected by your dashboard.html:
    filenames, ai_scores, authenticity, blockchain, timestamps, hashes
    Only uses per-upload JSON files in REPORT_FOLDER (dicts containing 'file').
    """
    import glob

    report_files = sorted(glob.glob(os.path.join(REPORT_FOLDER, "*.json")),
                          key=lambda p: os.path.getmtime(p),
                          reverse=True)

    filenames = []
    ai_scores = []
    authenticity = []
    blockchain = []
    hashes = []
    timestamps = []

    for full in report_files:
        try:
            with open(full, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception as e:
            # skip unreadable json
            print(f"⚠️ Skipping {full} (cannot load JSON): {e}")
            continue

        # Only accept dict-shaped per-upload reports
        if not isinstance(data, dict):
            continue
        if 'file' not in data:
            continue

        # Extract values (use safe defaults if missing)
        fname = data.get('file')
        ai = data.get('ai_score')
        auth = data.get('authenticity_score')
        bc = data.get('blockchain_verified', False)
        h = data.get('hash', '')
        # timestamp: prefer generated_at then fallback to filename timestamp
        if data.get('generated_at'):
            try:
                dt = datetime.datetime.fromisoformat(data['generated_at'])
                ts = dt.strftime("%d-%b-%Y %H:%M:%S")
            except Exception:
                ts = str(data['generated_at'])
        else:
            # try to infer from report file name like report_YYYYMMDD_HHMMSS.json
            try:
                base = os.path.basename(full)
                ts_part = base.split("report_")[-1].split(".json")[0]
                ts = datetime.datetime.strptime(ts_part, "%Y%m%d_%H%M%S").strftime("%d-%b-%Y %H:%M:%S")
            except Exception:
                ts = datetime.datetime.fromtimestamp(os.path.getmtime(full)).strftime("%d-%b-%Y %H:%M:%S")

        filenames.append(fname)
        # ensure numeric values (or null) are serializable to template/JS
        try:
            ai_scores.append(float(ai) if ai is not None else None)
        except Exception:
            ai_scores.append(None)
        try:
            authenticity.append(float(auth) if auth is not None else None)
        except Exception:
            authenticity.append(None)

        blockchain.append("Verified" if bool(bc) else "Not Verified")
        hashes.append(str(h))
        timestamps.append(ts)

    # If nothing found, show friendly message
    if len(filenames) == 0:
        return "<h3>No per-upload reports found yet. Please upload a file first.</h3>"

    # counts for top stats: treat ai_score < 0.5 as real
    real_count = sum(1 for v in ai_scores if (v is not None and v < 0.5))
    fake_count = len([v for v in ai_scores if v is not None]) - real_count

    return render_template(
        "dashboard.html",
        filenames=filenames,
        ai_scores=ai_scores,
        authenticity=authenticity,
        blockchain=blockchain,
        real_count=real_count,
        fake_count=fake_count,
        timestamps=timestamps,
        hashes=hashes
    )
@app.route('/result')
def result():
    return render_template('result.html')


if __name__ == '__main__':
    app.run(debug=True)
