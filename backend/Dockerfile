FROM python:3.8.5
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get -y install sudo
RUN pip3 install -r requirements.txt --no-cache-dir
COPY . .
CMD gunicorn backend.wsgi:application --bind 0.0.0.0:8000