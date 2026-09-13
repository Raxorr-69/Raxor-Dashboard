# One Render Web Service: build React, then serve it from FastAPI.
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend

# The React bundle is environment-neutral. Discord's public OAuth client id
# is injected at runtime by FastAPI at /config.js; the client secret is never
# sent to the browser or included in the image.

COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

WORKDIR /app/backend

EXPOSE 10000

CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"
