FROM python:3.10-slim

WORKDIR /app

COPY line_reply_service.py .

RUN pip install flask requests python-dotenv flask_sqlalchemy psycopg2-binary flask_bcrypt line-bot-sdk

CMD ["python", "line_reply_service.py"]
