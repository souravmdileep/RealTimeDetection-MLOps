FROM python:3.10-slim

WORKDIR /app

COPY alert_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alert_service/ ./alert_service/

EXPOSE 8001

# Run on port 8001 (Port 8000 is taken by Backend)
CMD ["uvicorn", "alert_service.app:app", "--host", "0.0.0.0", "--port", "8001"]
