# Use a minimal Python base image
FROM python:3.9-slim

# Set environment variables to prevent Python from writing .pyc files and to prevent buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    bash \
    chromium \
    libglib2.0-0 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxrandr2 \
    libasound2 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libnspr4 \
    libpango-1.0-0 \
    libxshmfence1 \
    xdg-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Playwright and dependencies
RUN pip install playwright && playwright install --with-deps chromium

# Copy the application code into the container
COPY . /app/

# Set environment variable for Chromium path to avoid issues with detection
ENV CHROME_BIN=/usr/bin/chromium

# Expose the Flask port
EXPOSE 5000

# Command to run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "300", "app:app"]
