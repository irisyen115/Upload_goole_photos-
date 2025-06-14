FROM python:3.10-slim

WORKDIR /app

COPY . /app

# 安裝需要的套件
RUN pip install flask requests python-dotenv flask_sqlalchemy psycopg2-binary flask_bcrypt line-bot-sdk Pillow

# 設定 PYTHONPATH
ENV PYTHONPATH=/app

# 啟動指令
CMD ["python", "app.py"]
