import numpy as np
import cv2
import logging
from pathlib import Path
import tensorflow as tf
import onnxruntime as ort

logger = logging.getLogger("backend")

BASE_DIR = Path(__file__).resolve().parent.parent

COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
    "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
    "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush"
]

class ModelManager:
    def __init__(self):
        self.loaded_version = None
        self.model = None
        self.session = None

    def load_model(self, version):
        if self.loaded_version == version:
            return

        if version == "v1":
            self.model = self._load_tf_model()
            self.session = None
            self.loaded_version = "v1"
            logger.info("Loaded baseline TensorFlow SSD MobileNet v2 model")

        elif version == "v2":
            self.session = self._load_yolo_onnx()
            self.model = None
            self.loaded_version = "v2"
            logger.info("Loaded improved YOLOv8n ONNX model")
        else:
            raise ValueError("Invalid model version")

    def _load_tf_model(self):
        # NEW: Use absolute path
        model_path = BASE_DIR / "models" / "v1"
        return tf.saved_model.load(str(model_path))

    def _load_yolo_onnx(self):
        # NEW: Load the Quantized (Int8) model
        model_path = BASE_DIR / "models" / "v2" / "yolov8m_int8.onnx"
        
        # Enable CPU specific optimizations
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        return ort.InferenceSession(str(model_path), sess_options)

    def predict(self, version, img):
        if version == "v1":
            return self._predict_ssd(img)
        elif version == "v2":
            return self._predict_yolo(img)
        else:
            raise ValueError("Invalid version")

    def _predict_ssd(self, img):
        # Resize to 300x300 expected by SSD MobileNet
        img_resized = cv2.resize(img, (300, 300))
        input_tensor = tf.convert_to_tensor(img_resized, dtype=tf.uint8)
        input_tensor = tf.expand_dims(input_tensor, 0)
        
        # Get the serving signature
        infer = self.model.signatures["serving_default"]
        outputs = infer(input_tensor)

        boxes = outputs['detection_boxes'][0].numpy()
        scores = outputs['detection_scores'][0].numpy()
        classes = outputs['detection_classes'][0].numpy().astype(int)

        height, width, _ = img.shape
        detections = []
        for i in range(len(scores)):
            if scores[i] < 0.5:
                continue
            
            # TF boxes are [ymin, xmin, ymax, xmax] normalized
            ymin, xmin, ymax, xmax = boxes[i]
            box = [xmin * width, ymin * height, (xmax - xmin) * width, (ymax - ymin) * height]

            class_idx = classes[i] - 1
            if class_idx < len(COCO_CLASSES):
                label = COCO_CLASSES[class_idx]
            else:
                label = "unknown"

            detections.append({
                "class": label,
                "score": float(scores[i]),
                "box": box
            })
        return detections

    def _predict_yolo(self, img):
        # Preprocessing
        original_h, original_w, _ = img.shape
        img_resized = cv2.resize(img, (640, 640))
        img_input = img_resized.transpose(2, 0, 1) # HWC -> CHW
        img_input = img_input[np.newaxis, :, :, :] / 255.0 # Normalize 0-1
        img_input = img_input.astype(np.float32)

        # Inference
        input_name = self.session.get_inputs()[0].name
        outputs = self.session.run(None, {input_name: img_input})[0]
        
        # YOLOv8 Output Shape: (1, 84, 8400) -> Transpose to (8400, 84)
        predictions = np.transpose(outputs[0])
        
        boxes = []
        confidences = []
        class_ids = []

        # Parse Predictions
        for pred in predictions:
            class_scores = pred[4:] # Classes start at index 4
            class_id = np.argmax(class_scores)
            confidence = class_scores[class_id]

            if confidence > 0.5:
                # YOLO box: [cx, cy, w, h] (normalized to 640x640)
                cx, cy, w, h = pred[0], pred[1], pred[2], pred[3]

                # Scale back to original image size
                x_scale = original_w / 640
                y_scale = original_h / 640
                
                width = w * x_scale
                height = h * y_scale
                left = (cx - w/2) * x_scale
                top = (cy - h/2) * y_scale

                boxes.append([int(left), int(top), int(width), int(height)])
                confidences.append(float(confidence))
                class_ids.append(class_id)

        # Apply Non-Maximum Suppression (NMS) using OpenCV
        indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

        final_detections = []
        if len(indices) > 0:
            for i in indices.flatten():
                final_detections.append({
                    "class": COCO_CLASSES[class_ids[i]],
                    "score": confidences[i],
                    "box": boxes[i]
                })

        return final_detections