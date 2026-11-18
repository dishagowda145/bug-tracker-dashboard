FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY . .
ENV PORT=5000
EXPOSE 5000
# Create a non-root user so the app does not run as root
RUN useradd -m appuser && chown -R appuser /app
USER appuser
CMD gunicorn --chdir backend --workers 2 --bind 0.0.0.0:$PORT wsgi:app
