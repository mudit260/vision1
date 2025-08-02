# Use an official Python image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y tesseract-ocr poppler-utils && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set Tesseract path explicitly (if needed)
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# Start the Gradio app
CMD ["python", "New_for_deploying.py"]
