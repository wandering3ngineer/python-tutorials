# Use the official Python image from the Docker Hub
FROM python:3.11.9-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy the code to the WORKDIR from the current  (second . is the WORKDIR)
COPY . .

# Install ffmpeg and other dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the necessary ports.
EXPOSE 8006

# Command to run the application in the shell
# sh -c <string> where <string> = "python llm.py"
CMD ["python", "tts.py"]
