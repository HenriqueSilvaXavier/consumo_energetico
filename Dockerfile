# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install OpenJDK 11
RUN apt-get update && apt-get install -y openjdk-11-jdk && apt-get clean

# Set JAVA_HOME environment variable
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set environment variables for Spark (optional, adjust as needed)
ENV SPARK_HOME=/opt/spark
ENV PATH=$SPARK_HOME/bin:$PATH

# Expose the port for Gradio
EXPOSE 7860

# Command to run the application
CMD ["python", "app.py"]
