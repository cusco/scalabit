FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for caching
COPY py-requirements/base.txt .

# Install dependencies
RUN pip install --no-cache-dir -r base.txt

# Copy source code
COPY src/ ./src/

# Copy action entrypoint
COPY action_entrypoint.py .
RUN chmod +x action_entrypoint.py

# Expose port for REST API mode
EXPOSE 5000

# Default entrypoint for GitHub Action
ENTRYPOINT ["python3", "action_entrypoint.py"]