# Use the official Python image from the Docker Hub
FROM python:3.11.9-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Flags to use libomp-dev for llama
ENV CFLAGS="-fopenmp"
ENV LDFLAGS="-fopenmp"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential cmake gcc g++ clang libomp-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the code to the WORKDIR from the current DIR
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the necessary ports. In this case when we 
# make a request of the llm we do so 
EXPOSE 8003

# Command to run the application in the shell
# sh -c <string> where <string> = "python llm.py"
CMD ["python", "llm.py"]
