# Use official Python image
FROM python:3.11-slim

ENV PYTHONPATH="/app"

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .

# Install system dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app/ app/

# Expose ports
EXPOSE 8000

# Start the app
# No CMD — just use docker-compose to define entrypoint per service