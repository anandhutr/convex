# Convex Studio Inventory System - Dockerfile
# Multi-stage build for production deployment

# Build stage
FROM python:3.9-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.9-slim

# Create non-root user for security
RUN groupadd -r inventory && useradd -r -g inventory inventory

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/inventory/.local

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads backups logs static templates && \
    chown -R inventory:inventory /app

# Switch to non-root user
USER inventory

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONPATH=/home/inventory/.local/lib/python3.9/site-packages

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application
CMD ["python", "app.py"] 