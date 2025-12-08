# Use lightweight Python
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (Required for OpenCV)
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt .
# Upgrade pip first (helps find binary wheels)
RUN pip install --upgrade pip

# Install requirements with binary preference and longer timeout
RUN pip install --no-cache-dir --prefer-binary --default-timeout=1000 -r requirements.txt

# Copy the rest of the backend code and necessary resources
COPY backend/ ./backend/
COPY evaluation/test_images/ ./evaluation/test_images/
COPY scripts/ ./scripts/

ENV PYTHONPATH=/app/backend

# Expose port
EXPOSE 8000

# Run the app using Uvicorn
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]