# Use Python 3.12 slim as the base image for better compatibility
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
# We install numpy first because some packages (like kiwipiepy) might need it during build-time requirement resolution
COPY requirements.txt .
RUN pip install --no-cache-dir "numpy<2.0.0" setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code and guide
COPY app.py .
COPY GUIDE.md .

# Expose the Streamlit port
EXPOSE 8501

# Command to run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
