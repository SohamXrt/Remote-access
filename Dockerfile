FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy relay server
COPY persistent_cloud_relay.py .

# Expose WebSocket port
EXPOSE 8765

# Run the relay server
CMD ["python3", "persistent_cloud_relay.py"]
