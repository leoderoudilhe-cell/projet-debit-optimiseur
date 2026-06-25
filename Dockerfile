# Image universelle — fonctionne sur Railway, Render, Fly.io, Hugging Face Spaces.
FROM python:3.12-slim

# Dépendances système minimales (reportlab n'a pas besoin de plus en slim)
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 1) Dépendances d'abord (cache Docker)
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install -r backend/requirements.txt

# 2) Code applicatif
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Dossier de stockage (PDFs + SQLite). Monter un volume ici pour persister.
ENV STORAGE_PATH=/app/storage/pdfs
RUN mkdir -p /app/storage/pdfs

# L'app lit les chemins relativement à backend/ (comme en dev local)
WORKDIR /app/backend

EXPOSE 8000
# $PORT est fourni par l'hébergeur (Railway/Render). Défaut 8000 en local.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
