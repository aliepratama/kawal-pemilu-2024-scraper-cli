# Use slim Python image for smaller size
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Playwright (minimal)
RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install --no-cache-dir pipenv

# Copy Pipfile and Pipfile.lock (if exists)
COPY Pipfile Pipfile* ./

# Install Python dependencies
RUN pipenv install --system --deploy --ignore-pipfile || pipenv install --system

# Install Playwright browsers (only chromium for minimal size)
RUN playwright install chromium && \
    playwright install-deps chromium

# Copy application code
COPY . .

# Create output directories
RUN mkdir -p output output_roi

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
CMD ["python", "cli.py"]
