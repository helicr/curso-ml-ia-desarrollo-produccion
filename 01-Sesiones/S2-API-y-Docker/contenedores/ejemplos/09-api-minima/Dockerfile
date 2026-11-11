FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY api.py .
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin apiuser
USER 10001
EXPOSE 8080
HEALTHCHECK --interval=3s --timeout=2s --start-period=1s --retries=2 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/salud', timeout=1)"
CMD ["python", "api.py"]
