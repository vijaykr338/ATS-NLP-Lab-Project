# Base image
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies (for pdfplumber)
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency file first (Docker cache optimization)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy language model
RUN python -m spacy download en_core_web_sm

# Copy project files
COPY src/ ./src
COPY models/ ./models
COPY Data/ ./Data
COPY static/ ./static

# Expose Flask port
EXPOSE 5000

# Run the Flask app
CMD ["python", "src/app.py"]