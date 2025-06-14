from service.synology_service import (
    save_photos_to_db_with_album, save_exist_db_with_person,
    save_photos_to_db_with_person, random_pick_from_person_database,
    randam_pick_from_album_database, save_exit_db_with_album
)
from lib.synlogy import list_photos_by_album, list_photos_by_person
from lib.google import get_service
from datetime import datetime, timedelta
import logging
from models.photo import Photo
from models.database import SessionLocal
from models.person import Person
import requests

logging.basicConfig(filename="error.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

def needs_sync_warning(person_photos, person_id, upload_photo_num):
    if not person_id:
        return {"photos": [], "messages": ["person_id 為空，無法處理"]}

    messages = []
    sync_warn = False

    if not person_photos and len(person_photos) <= upload_photo_num:
        msg = f"⚠️ 找不到 person_id={person_id} 的照片，將花時間從全部資料中挑選。"
        messages.append(msg)
        sync_warn = True
    if not messages:
        messages.append(f"✅ person_id={person_id} 的照片已經上傳完成，數量為 {upload_photo_num} 張。")
    return sync_warn, messages


import threading
from config.config import Config

def background_sync_and_upload(auth, person_id, upload_photo_num, token):
    logging.info(f"開始背景同步與上傳 person_id={person_id}")

    person_photo_list = list_photos_by_person(auth=auth, person_id=person_id)
    if not person_photo_list:
        logging.error(f"⚠️ 人員 {person_id} 沒有同步到任何照片")
        return

    save_photos_to_db_with_person(person_photo_list, person_id)
    random_photos = random_pick_from_person_database(person_id=person_id, limit=upload_photo_num)
    if not random_photos:
        logging.error(f"⚠️ 人員 {person_id} 的隨機照片選取為空")
        return

    exit_person_filename = [photo.filename for photo in save_exist_db_with_person(person_id=person_id, photos=random_photos)]
    logging.error(f"現存於 Google 相簿照片檔名: {exit_person_filename}")
    logging.info(f"✅ person_id={person_id} 同步與上傳完成")
    requests.post(f"{Config.SERVER_URL}/api/line/notify", json={
        "token": token,
        "message": "✅ 你的人員資料已完成同步！請重新操作。"
    })

import threading

def get_photos_upload_to_album(auth, person_id, album_id, upload_photo_num, token):
    if not person_id:
        logging.error("⚠️ person_id 為空，無法處理")
        return {"photos": [], "messages": ["person_id 為空，無法處理"]}

    db = SessionLocal()
    person_photos = db.query(Photo).join(Person, Person.photo_id == Photo.item_id).filter(Person.person_id == person_id).all()
    if not person_photos:
        logging.error(f"⚠️ 找不到 person_id={person_id} 的照片，將花時間從全部資料中挑選。")

    sync_warn, messages = needs_sync_warning(
        person_photos,
        person_id,
        upload_photo_num
    )

    if sync_warn:
        logging.warning(f"⚠️ 人員 {person_id} 需要同步，將於背景延遲執行")

        # ✅ 用 Timer 延遲執行，確保回應先發再同步
        threading.Timer(
            interval=2,  # 200ms 後再執行
            function=background_sync_and_upload,
            args=(auth, person_id, upload_photo_num, token)
        ).start()

        # ✅ 主流程立即回應
        return {
            "photos": [],
            "messages": ["✅ 任務已提交，系統將在背景同步資料與上傳照片，請稍候再試"]
        }

    # 📌 如果不需要同步就照正常流程回傳照片
    person_photo_list = list_photos_by_person(auth=auth, person_id=person_id, limit=upload_photo_num)
    random_photos = random_pick_from_person_database(person_id=person_id, limit=upload_photo_num)

    if not person_photo_list or not random_photos:
        return {"photos": [], "messages": ["沒有可上傳的照片"]}

    save_photos_to_db_with_person(person_photo_list, person_id)
    exit_person_filename = [photo.filename for photo in save_exist_db_with_person(person_id=person_id, photos=random_photos)]
    logging.error(f"現存於 Google 相簿照片檔名: {exit_person_filename}")

    return {
        "photos": random_photos,
        "messages": messages
    }

def delete_photos_by_filename(creds, album_id, filenames):
    service = get_service(creds)
    photos = []
    next_page_token = None

    while True:
        response = service.mediaItems().search(body={
            "albumId": album_id,
            "pageSize": 100,
            "pageToken": next_page_token
        }).execute()

        items = response.get("mediaItems", [])
        for item in items:
            filename = item.get("filename")
            media_id = item.get("id")
            if filename in filenames:
                photos.append(media_id)

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    logging.error(f"🗑️ 符合條件要刪除的照片ID數量：{len(photos)}")

    for photo_id in photos:
        try:
            service.mediaItems().delete(mediaItemId=photo_id).execute()
            logging.error(f"✅ 已刪除：{photo_id}")
        except Exception as e:
            logging.error(f"❌ 刪除失敗：{photo_id} - {e}")
