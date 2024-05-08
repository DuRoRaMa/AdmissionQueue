FROM python:3-alpine
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
WORKDIR /app/admission
CMD python manage.py migrate; python manage.py runserver 0.0.0.0:8000 --settings=admission.settings.prod