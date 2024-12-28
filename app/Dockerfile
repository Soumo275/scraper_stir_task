# Use a smaller base image for Python runtime
FROM python:3.9-alpine

# Set environment variables to prevent Python from writing .pyc files and to prevent buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install required system dependencies in a minimal way
RUN apk update && apk add --no-cache \
    chromium \
    chromium-chromedriver \
    curl \
    bash \
    libc6-compat \
    && rm -rf /var/cache/apk/*

# Install Playwright dependencies and set up Playwright
RUN pip install --upgrade pip && \
    pip install playwright && \
    playwright install --with-deps chromium

# Copy the requirements file and install Python dependencies
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Set environment variable for Chromium path to avoid any issues with path detection
ENV CHROME_BIN=/usr/bin/chromium

# Expose the port Flask will run on
EXPOSE 5000

# Command to run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "300", "app:app"]
