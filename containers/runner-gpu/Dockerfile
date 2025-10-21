# Use a more recent PyTorch base image with better caching
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-devel

WORKDIR /workspace

# Set environment variables for better caching and performance
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/workspace/.cache

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-distutils \
    && rm -rf /var/lib/apt/lists/*

# Install pip for Python 3.11
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Install Python dependencies in separate layers for better caching
RUN python3.11 -m pip install --no-cache-dir --upgrade pip

# Install core dependencies first (these change less frequently)
RUN python3.11 -m pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    pillow==10.1.0

# Install ML dependencies (these are larger and change more frequently)
RUN python3.11 -m pip install --no-cache-dir \
    diffusers==0.25.0 \
    transformers==4.36.0 \
    accelerate==0.25.0 \
    safetensors==0.4.1

# Copy application code
COPY inference_server.py .

# Create cache directory
RUN mkdir -p /workspace/.cache

# Note: Model download is now handled at runtime in the application
# This prevents build stalls and allows for better caching

EXPOSE 8000

CMD ["python3.11", "-m", "uvicorn", "inference_server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
