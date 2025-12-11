# Use lightweight Python
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (Required for OpenCV + Model Downloading)
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

# ### NEW: Explicitly install Ultralytics for the 'yolo' CLI command
RUN pip install ultralytics

# -------------------------------------------------------------------
#  MODEL DOWNLOAD SECTION
# -------------------------------------------------------------------

# 1. Prepare Directories
RUN mkdir -p /app/backend/models/v1
RUN mkdir -p /app/backend/models/v2

# 2. V1: SSD MobileNet (Download & Extract)
RUN wget -O /tmp/ssd.tar.gz http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v2_coco_2018_03_29.tar.gz && \
    tar -xzvf /tmp/ssd.tar.gz -C /tmp && \
    mv /tmp/ssd_mobilenet_v2_coco_2018_03_29/saved_model/* /app/backend/models/v1/ && \
    rm -rf /tmp/ssd*

# 3. V2: YOLOv8 Medium (Download & Export)
# Download the 'Medium' weights (High Accuracy)
RUN wget -O /app/backend/models/v2/yolov8m.pt https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8m.pt

# Export to ONNX (Standard Format)
# This generates: /app/backend/models/v2/yolov8m.onnx
RUN yolo export model=/app/backend/models/v2/yolov8m.pt format=onnx opset=12

# -------------------------------------------------------------------

# Copy the rest of the backend code
COPY backend/ ./backend/
COPY evaluation/test_images/ ./evaluation/test_images/
COPY scripts/ ./scripts/

ENV PYTHONPATH=/app/backend

# Expose port
EXPOSE 8000

# Run the app using Uvicorn
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]