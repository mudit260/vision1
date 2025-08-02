#!/usr/bin/env bash

# Install Tesseract
apt-get update && apt-get install -y tesseract-ocr

# Install Python packages
pip install -r requirements.txt
