# Dockerfile for MCP Servers

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Make ports 8000 and 8001 available to the world outside this container
EXPOSE 8000
EXPOSE 8001

# Define environment variables
ENV SEC_API_USER_AGENT="Your Name your.email@example.com"

# Run the main server entrypoint when the container launches
CMD ["python", "src/main.py"]
