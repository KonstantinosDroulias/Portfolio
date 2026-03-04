# ═══════════════════════════════════════════════════════════
# Stage 1 — Build Tailwind CSS
# ═══════════════════════════════════════════════════════════
FROM node:20-alpine AS frontend

WORKDIR /app

# Install Node dependencies (layer-cached unless package files change)
COPY package.json package-lock.json* ./
RUN npm ci

# Copy only the files Tailwind needs to scan for class names
COPY static/src/ ./static/src/
COPY templates/ ./templates/
COPY website/ ./website/
COPY projects/ ./projects/

RUN npm run build:css


# ═══════════════════════════════════════════════════════════
# Stage 2 — Python application
# ═══════════════════════════════════════════════════════════
FROM python:3.12-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies (layer-cached unless requirements change)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Overlay the compiled CSS from the frontend stage
COPY --from=frontend /app/static/dist/ ./static/dist/

# Create directories written at runtime
RUN mkdir -p staticfiles media

EXPOSE 8000

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
