import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    LINE_PUSH_URL = os.getenv("LINE_PUSH_URL")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    LINE_REPLY_URL=os.getenv("LINE_REPLY_URL")
    SERVER_URL=os.getenv("SERVER_URL")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
