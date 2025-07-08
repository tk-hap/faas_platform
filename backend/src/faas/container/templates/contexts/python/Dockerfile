FROM python:3.11-slim

# Set environment vars for production
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

COPY . /app

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "func:app"]

