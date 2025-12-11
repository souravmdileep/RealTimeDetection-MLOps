# Use lightweight Python
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (Required for OpenCV + Model Downloading)
# Added 'wget' and 'tar' to download and extract AI models
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    wget \
    tar \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt .
# Upgrade pip first (helps find binary wheels)
RUN pip install --upgrade pip

# Install requirements with binary preference and longer timeout
RUN pip install --no-cache-dir --prefer-binary --default-timeout=1000 -r requirements.txt

# -------------------------------------------------------------------
#  MODEL DOWNLOAD SECTION (Fixes 500 Internal Server Error)
# -------------------------------------------------------------------

# 1. Prepare Directories
RUN mkdir -p /app/backend/models/v1
RUN mkdir -p /app/backend/models/v2

# 2. Download & Install 'v1' (SSD MobileNet V2)
# We download the tarball, extract it, and move the 'saved_model' folder contents to /models/v1
RUN wget -O /tmp/ssd.tar.gz http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v2_coco_2018_03_29.tar.gz && \
    tar -xzvf /tmp/ssd.tar.gz -C /tmp && \
    mv /tmp/ssd_mobilenet_v2_coco_2018_03_29/saved_model/* /app/backend/models/v1/ && \
    rm -rf /tmp/ssd*

# 3. Download & Install 'v2' (YOLOv8 Nano)
# We download the weights file directly from Ultralytics
RUN wget -O /app/backend/models/v2/yolov8n.pt https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt

# -------------------------------------------------------------------

# Copy the rest of the backend code (app.py, utils/, etc.)
COPY backend/ ./backend/
COPY evaluation/test_images/ ./evaluation/test_images/
COPY scripts/ ./scripts/

ENV PYTHONPATH=/app/backend

# Expose port
EXPOSE 8000

# Run the app using Uvicorn
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]