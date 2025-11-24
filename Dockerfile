ARG BUILD_FOR_TEST=false

# Use official Python 3.13 base
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install core dependencies (always needed)
RUN apt-get update && apt-get install -y \
    # Packages like git, curl, or base networking utilities
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Conditional installation of heavy graphics/web server packages
RUN if [ "$BUILD_FOR_TEST" = "false" ]; then \
    apt-get update && apt-get install -y \
        nginx \
        libgl1 \
        libglib2.0-0 \
        # ... any other heavy packages ...
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*; \
    fi

# Copy all project files into the container
COPY . .

# Install Python dependencies (uv & your requirements)
RUN pip install uv && uv sync

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI app
CMD ["sh", "-c", "if [ \"$APP_ENV\" = 'dev' ]; then uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload; else uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000; fi"]
