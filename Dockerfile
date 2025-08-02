FROM python:3.10-slim

# Install system packages including tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy code
COPY . /app

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Set the default command
CMD ["python", "New_for_deploying.py"]
