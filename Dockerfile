# Use the official Python image as a base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1  
ENV PYTHONUNBUFFERED=1  

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt /app/

# Upgrade pip version
RUN pip install --upgrade pip

# Install dependencies
RUN pip install -r requirements.txt

# Copy the entire project into the container
COPY . /app

# Expose the port that the Django app runs on
EXPOSE 9000

# Run Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:9000"]