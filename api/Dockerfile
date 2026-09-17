FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN addgroup --system monarch && adduser --system --ingroup monarch monarch

COPY pyproject.toml ./
COPY app ./app
RUN python -m pip install --no-cache-dir .

COPY docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x ./docker-entrypoint.sh \
    && mkdir -p /data/quote_uploads \
    && chown -R monarch:monarch /app /data

USER monarch

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=2)" || exit 1

ENTRYPOINT ["./docker-entrypoint.sh"]
