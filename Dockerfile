# Use official Python 3.13 base
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y nginx && apt-get clean

# Copy all project files into the container
COPY . .

# Install uv and sync the project
RUN pip install uv && uv sync

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI app
CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
