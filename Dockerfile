FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN mkdir -p /app/data && chown -R 10001:10001 /app
USER 10001:10001
EXPOSE 8766
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8766", "--workers", "1"]
