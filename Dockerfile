FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer cache)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./

# Copy frontend into static/ so FastAPI serves it
COPY frontend/ ./static/

EXPOSE 85

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "85"]
