# ============================================================
# Dockerfile — Python Flask Application Container
# ============================================================
# Stage: Single-stage production image based on slim Python
# Container runs on port 5000 and talks to MySQL via Compose network
# ============================================================

FROM python:3.12-slim

# Set environment variables
# - PYTHONDONTWRITEBYTECODE: Don't write .pyc bytecode files (cleaner container)
# - PYTHONUNBUFFERED: Ensures print/log statements show immediately in Docker logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory inside the container filesystem
WORKDIR /app

# Install system dependencies first (separate layer = better cache)
# default-libmysqlclient-dev and pkg-config are needed for PyMySQL's crypto dependency
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy ONLY the requirements file first — Docker caches this layer.
# If only app code changes (not requirements), Docker reuses the pip install layer.
COPY app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the application source code
COPY app/ .

# Expose the port Flask listens on inside the container
EXPOSE 5000

# Healthcheck — Docker will probe this every 30s to know if the container is healthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Run the Flask application using Gunicorn (production-grade WSGI server)
# - 1 worker for a single-machine demo; scale to 2-4 per CPU core in production
# - Binds to 0.0.0.0 so Docker port mapping from host can reach it
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "120", "app:app"]
