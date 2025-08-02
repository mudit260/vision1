FROM python:3.10-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variable so Gradio binds to 0.0.0.0
ENV GRADIO_SERVER_NAME=0.0.0.0

# Expose default Gradio port
EXPOSE 7860

# Run your app
CMD ["python", "New_for_deploying.py"]
