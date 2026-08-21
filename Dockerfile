FROM python:3.10-slim

# Prevents Python from writing .pyc files and enables logs to stdout
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .
RUN chmod +x entrypoint.sh && sed -i 's/\r$//' entrypoint.sh

# Ensure directories exist
RUN mkdir -p static templates

# Expose Gunicorn port
EXPOSE 5000

# Start app with Gunicorn (4 workers, 2 threads per worker)
CMD ["./entrypoint.sh"]
