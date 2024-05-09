FROM python:3-alpine
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
WORKDIR /app/admission
CMD python manage.py collectstatic; python manage.py migrate; daphne -b 0.0.0.0 -p 8000 admission.asgi:application