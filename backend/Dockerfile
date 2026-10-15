# syntax=docker/dockerfile:1.7
FROM python:3.14-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

FROM base AS deps
COPY requirements.txt requirements-dev.txt ./
ARG INSTALL_DEV=false
RUN pip install -r requirements.txt && if [ "$INSTALL_DEV" = "true" ]; then pip install -r requirements-dev.txt; fi

FROM deps AS runtime
COPY . .
# Run as an unprivileged user with a read-only app directory.
RUN useradd --system --uid 10001 --home /nonexistent wof \
    && DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput --settings=wof.settings.dev \
    && chown -R root:root /app && chmod -R a-w /app
USER wof
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz').status==200 else 1)"
CMD ["gunicorn", "wof.wsgi", "--bind", "0.0.0.0:8000", "--workers", "3", "--max-requests", "2000", "--max-requests-jitter", "200", "--access-logfile", "-"]
