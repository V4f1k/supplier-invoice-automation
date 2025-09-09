# Multi-stage Dockerfile for Invoice OCR Service

# Stage 1: Build stage - Install dependencies
FROM python:3.11.9-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    pkg-config \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libtiff-dev \
    libopenjp2-7-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==2.1.4

# Copy dependency files
COPY pyproject.toml ./

# Install project dependencies
# Configure poetry to not create virtual environment and install to system
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# Stage 2: Runtime stage
FROM python:3.11.9-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Install runtime system libraries required by Pillow/PyMuPDF/Surya-OCR
RUN apt-get update && apt-get install -y \
    libjpeg62-turbo \
    zlib1g \
    libpng16-16 \
    libtiff6 \
    libopenjp2-7 \
    libwebp7 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser ./app ./app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
