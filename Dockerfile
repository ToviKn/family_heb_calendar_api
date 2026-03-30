FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip \
 && pip install --default-timeout=100 --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:${PORT:-8000} main:app"]
