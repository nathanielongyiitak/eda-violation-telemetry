# --- Stage 1: Build & Dependency Gathering ---
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# TASK 1: Install dependencies into a localized wheel or virtualenv directory 
# Ensure no cache directory overhead is preserved.
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# --- Stage 2: Final Secure Production Runtime ---
FROM python:3.11-slim

WORKDIR /app

# TASK 1: Create a non-privileged system user/group to prevent container root exploits
RUN groupadd -r appgroup && useradd -r -g appgroup -u 1000 appuser

COPY --from=builder /app/wheels /tokens/wheels
COPY --from=builder /app/requirements.txt .

# Install the pre-compiled wheels natively
RUN pip install --no-index --find-links=/tokens/wheels -r requirements.txt \
    && rm -rf /tokens

COPY --chown=appuser:appgroup . .

# Enforce non-root execution context
USER appuser

EXPOSE 8000

CMD ["python", "log_parser.py"]