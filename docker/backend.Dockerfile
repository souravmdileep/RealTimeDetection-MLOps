# Use lightweight Python
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    wget \
    tar \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --prefer-binary --default-timeout=1000 -r requirements.txt

# Explicitly install Ultralytics for export
RUN pip install ultralytics

# -------------------------------------------------------------------
#  MODEL DOWNLOAD & QUANTIZATION SECTION
# -------------------------------------------------------------------

# 1. Prepare Directories
RUN mkdir -p /app/backend/models/v1
RUN mkdir -p /app/backend/models/v2

# 2. V1: SSD MobileNet (Standard)
RUN wget -O /tmp/ssd.tar.gz http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v2_coco_2018_03_29.tar.gz && \
    tar -xzvf /tmp/ssd.tar.gz -C /tmp && \
    mv /tmp/ssd_mobilenet_v2_coco_2018_03_29/saved_model/* /app/backend/models/v1/ && \
    rm -rf /tmp/ssd*

# 3. V2: YOLOv8 Medium (Download & Quantize)
# Download the 'Medium' weights
RUN wget -O /app/backend/models/v2/yolov8m.pt https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8m.pt

# Export with Int8 Quantization
# Note: This will automatically download 'coco128.yaml' for calibration data
RUN yolo export model=/app/backend/models/v2/yolov8m.pt format=onnx int8=True opset=12

# RENAME STEP: Ultralytics outputs "yolov8m-int8.onnx" (hyphen)
# Your code expects "yolov8m_int8.onnx" (underscore). We fix that here:
RUN mv /app/backend/models/v2/yolov8m-int8.onnx /app/backend/models/v2/yolov8m_int8.onnx

# -------------------------------------------------------------------

# Copy the rest of the backend code
COPY backend/ ./backend/
COPY evaluation/test_images/ ./evaluation/test_images/
COPY scripts/ ./scripts/

ENV PYTHONPATH=/app/backend
EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]