FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for caching
COPY py-requirements/base.txt .

# Install dependencies
RUN pip install --no-cache-dir -r base.txt

# Copy source code
COPY src/ ./src/

# Copy action entrypoint to a new place
COPY action_entrypoint.py /entrypoint/action_entrypoint.py
RUN chmod +x /entrypoint/action_entrypoint.py

ENV PYTHONPATH=/app

# Expose port for REST API mode
EXPOSE 5000

# Default entrypoint for GitHub Action
ENTRYPOINT ["python3", "/entrypoint/action_entrypoint.py"]