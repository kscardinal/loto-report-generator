# Use official Python 3.13 base
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for OpenCV + nginx
RUN apt-get update && apt-get install -y \
    nginx \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy all project files into the container
COPY . .

# Install Python dependencies (uv & your requirements)
RUN pip install uv && uv sync

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI app
CMD ["sh", "-c", "if [ \"$APP_ENV\" = 'dev' ]; then uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload; else uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000; fi"]
