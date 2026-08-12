FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements first (Docker caches this layer separately)
# This means if only your code changes but not requirements,
# Docker will not reinstall all packages on every rebuild
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY . .

# Tell Docker which port the app listens on
EXPOSE 8000

# Command to start the server
# --host 0.0.0.0 means listen on all network interfaces (required inside Docker)
# --reload means the server restarts automatically when code changes (development only)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
