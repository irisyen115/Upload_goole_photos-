import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SYNO_URL = os.getenv("SYNO_URL")
    SYNO_ACCOUNT = os.getenv("SYNO_ACCOUNT")
    SYNO_PASSWORD=os.getenv("SYNO_PASSWORD")
    SYNO_FID=os.getenv("SYNO_FID")
    SYNO_TIMEZONE=os.getenv("SYNO_TIMEZONE")
    SYNO_DOWNLOAD_DIR=os.getenv("SYNO_DOWNLOAD_DIR")
    LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
    SERVER_URL = os.getenv("SERVER_URL")
    ALBUM_URL=SERVER_URL + "/downloaded_albums"
    IMG_URL=SERVER_URL + "/images"