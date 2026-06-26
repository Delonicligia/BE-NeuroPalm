FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY app/ ./app/

# Create necessary directories for uploads and logs
RUN mkdir -p uploads/sawit logs

# Adjust permissions for non-root execution
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Menggunakan uvicorn secara langsung (single-process) untuk menghemat RAM di Render (Limit 512MB)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
