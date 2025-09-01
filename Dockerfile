FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY py-requirements/base.txt .

# Install dependencies
RUN pip install --no-cache-dir -r base.txt

# Copy source code
COPY src/ ./src/

# Expose port
EXPOSE 5000

# Run the application
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "5000"]