# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container at /app
# This includes app.py, templates/, and static/
COPY . .

# Expose the port that Flask will run on
EXPOSE 5000

# Define environment variable for Flask (important for Flask apps)
ENV FLASK_APP=app.py

# Run the Flask application
# The command 'flask run --host=0.0.0.0' makes the app accessible from outside the container
CMD ["flask", "run", "--host=0.0.0.0"]