FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Build static assets so WhiteNoise can serve them when DEBUG=False.
RUN python manage.py collectstatic --noinput

EXPOSE 7860

# Single worker: the ~1.5 GB TF process + model loads once, not per worker.
# Threads give request concurrency; the get_model() lock keeps inference safe.
# Long timeout covers the cold model download + load on the first request.
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:7860", \
     "--workers", "1", "--threads", "4", "--timeout", "180"]
