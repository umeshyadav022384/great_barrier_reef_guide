FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy static files
COPY src/ ./src/
COPY public/ ./public/

# Expose port
EXPOSE 8080

# Run Python HTTP server
CMD ["python", "-m", "http.server", "8080", "--directory", "src"]