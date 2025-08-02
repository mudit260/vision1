FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy app code
COPY . /app

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Render will use
ENV PORT 7860
EXPOSE 7860

# Start your app
CMD ["python", "New_for_deploying.py"]
