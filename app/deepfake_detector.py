import tensorflow as tf
import numpy as np
import cv2

MODEL_PATH = 'model/deepfake_model.h5'

class DeepfakeDetector:
    def __init__(self, model_path=MODEL_PATH):
        try:
            self.model = tf.keras.models.load_model(model_path)
        except Exception as e:
            print('Warning: could not load model:', e)
            self.model = None

    def extract_frames(self, video_path, num_frames=8):
        cap = cv2.VideoCapture(video_path)
        frames = []
        length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if length <= 0:
            length = num_frames
        indices = np.linspace(0, max(0,length-1), num_frames, dtype=int)
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame)
        cap.release()
        return frames

    def predict_video(self, video_path):
        if self.model is None:
            # Demo fallback: return 0.5 (uncertain)
            return 0.5
        frames = self.extract_frames(video_path, num_frames=8)
        if len(frames) == 0:
            return 0.5  # uncertain
        processed = []
        for f in frames:
            f = cv2.resize(f, (224,224))
            f = f.astype('float32')/255.0
            processed.append(f)
        X = np.stack(processed, axis=0)
        preds = self.model.predict(X, verbose=0)
        score = float(np.mean(preds))
        return score
