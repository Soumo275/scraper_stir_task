# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables for non-interactive installations
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for Chrome and Xvfb
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libnss3 \
    libx11-xcb1 \
    libgbm1 \
    xdg-utils \
    libgtk-3-0 \
    libxss1 \
    libxtst6 \
    xorg \
    libgconf-2-4 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome stable
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb && \
    apt-get install -f && \
    rm google-chrome-stable_current_amd64.deb

# Install ChromeDriver
RUN npm install -g chromedriver

# Set environment variable for headless Chrome
ENV DISPLAY=:99

# Install Python dependencies
COPY requirements.txt /app/
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app

# Expose the application on port 5000
EXPOSE 5000

# Set the default command to run the Flask app
CMD ["python", "app.py"]
