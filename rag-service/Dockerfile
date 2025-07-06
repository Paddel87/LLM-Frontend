FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt ./

# Install PyTorch CPU-only first (much faster, smaller)
RUN pip install --no-cache-dir torch==2.1.1+cpu --index-url https://download.pytorch.org/whl/cpu

# Install other requirements
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# Set environment variables for CPU-only operation
ENV CUDA_VISIBLE_DEVICES=""
ENV OMP_NUM_THREADS=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]