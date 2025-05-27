# Stage 1: Builder - Install Python dependencies
# This stage installs all necessary Python packages and their build dependencies.
# Using python:3.9-slim-buster provides a good balance between size and compatibility.
FROM python:3.9-slim-buster as builder

# Set the working directory inside the container
WORKDIR /app

# Install system-level build dependencies required by some Python packages (e.g., Gunicorn)
# --no-install-recommends helps keep the image smaller by avoiding unnecessary packages.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/* # Clean up apt cache to reduce image size

# Copy the requirements file into the builder stage
COPY requirements.txt .

# Install Python packages using pip wheel to cache wheels in a specified directory.
# This makes subsequent builds faster if requirements.txt doesn't change.
# --no-deps ensures only direct dependencies are downloaded at this stage.
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Final - Create the lightweight production image
# This stage builds the final production image by copying only the essential components.
FROM python:3.9-slim-buster

# Set the working directory for the application
WORKDIR /app

# Create a dedicated non-root user 'appuser' for security best practices.
# Running applications as root is a security risk.
RUN adduser --system --group appuser
USER appuser

# Copy the pre-built Python package wheels from the builder stage and install them.
# This avoids needing build tools in the final image, reducing its size.
COPY --from=builder /app/wheels /app/wheels
# Gunicorn executable is also copied from the builder stage if installed in a standard path.
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/
# Install the packages from the copied wheels.
RUN pip install --no-cache /app/wheels/*

# Copy the application code (app.py, templates/, static/) into the container.
COPY . .

# Expose the port that Gunicorn will bind to.
# This tells Docker which port the container listens on at runtime.
EXPOSE 5000

# Command to run the application using Gunicorn.
# 'gunicorn' is the WSGI server.
# '--workers 2': Sets the number of worker processes. A common recommendation is (2 * CPU_CORES) + 1.
#                Adjust this based on your server's resources.
# '--bind 0.0.0.0:5000': Binds Gunicorn to all network interfaces on port 5000.
# 'app:shivshakti_invoice_app': Specifies that Gunicorn should run the Flask application
#                              instance named 'shivshakti_invoice_app' found in 'app.py'.
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "app:shivshakti_invoice_app"]