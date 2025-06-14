FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN apt update ; apt install -y vim curl

COPY . .

ENV PYTHONPATH=/app

CMD ["python", "app.py"]
