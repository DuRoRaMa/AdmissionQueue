FROM python:3.12
ENV PYTHONUNBUFFERED=1
ENV REDIS_HOST=redis
ENV POSTGRES_HOST=pgdb
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
WORKDIR /app/admission
CMD make collectstatic migrate run.server.prod