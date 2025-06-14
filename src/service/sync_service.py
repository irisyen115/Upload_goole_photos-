import os, json, threading, time, queue
from lib.synlogy import login, list_people, thumb_photo, download_photo
from lib.google import (
    get_service, get_or_create_album, add_photos_to_album,
    upload_photo_bytes
)
from service.google_service import get_photos_upload_to_album
from delete_photo import delete_all_photos_from_album
from flask import jsonify
from config.config import Config
from service.batch_service import create_new_batch
import logging
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(filename="error.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

DOWNLOAD_DIR = Config.SYNO_DOWNLOAD_DIR
IMG_URL = Config.IMG_URL
ACCOUNT = Config.SYNO_ACCOUNT
PASSWORD = Config.SYNO_PASSWORD
FID = Config.SYNO_FID
TIMEZONE = Config.SYNO_TIMEZONE
NUM_DOWNLOAD_THREADS = 16
NUM_UPLOAD_THREADS = 16

download_queue = queue.Queue()
photo_queue = queue.Queue()
notify_queue = queue.Queue()
token_map = {}

def update_people_list(auth):
    if not auth:
        logging.error("Synology 登入失敗，請檢查帳號密碼或網路連線")
        return []

    try:
        people_list = list_people(auth, 8)
        if not people_list:
            logging.error("無法獲取人員列表，請檢查 Synology 服務是否正常")
            return []
        logging.info(f"成功獲取 {len(people_list)} 人員資料")
        result_list = []
        for person in people_list:
            thumb_photo(person['id'], person['additional']['thumbnail']['cache_key'], auth)
            result_list.append({
                "name": person['name'],
                "ID": person['id'],
                "img": f"{IMG_URL}/{person['id']}.jpg"
            })

        return result_list
    except Exception as e:
        logging.exception("⚠️ 更新人員資料過程中發生錯誤")
        return []

def handle_sync(request, creds, session):
    try:
        data = request.get_json(force=True)
    except Exception as e:
        logging.error("JSON 解析失敗: %s", str(e))
        return jsonify({"error": "無法解析 JSON，請檢查資料格式"}), 400

    person_id = request.args.get('personID') or data.get('personID')
    if person_id:
        logging.error(f"同步人員 ID: {person_id}")
    else:
        logging.error("請求中未提供 personID")
        return jsonify({"error": "請提供 personID"}), 400
    album_id = data.get("albumID")
    album_name = data.get("albumName") or os.getenv("DEFAULT_ALBUM_NAME", "My New Album")
    num_photos = data.get("numPhotos")
    token = request.args.get('token') or data.get('token')
    if not token:
        token = data.get("token")
    else:
        logging.info(f"使用提供的 token: {token}")

    if not person_id and not album_id:
        return jsonify({"error": "請提供 personID 或 albumID"}), 400

    start_time = time.time()
    auth = session.get('auth')
    if not auth:
        logging.error("Synology 登入狀態: False")
        auth = login(ACCOUNT, PASSWORD, FID, TIMEZONE)
        session['auth'] = auth
    logging.error(f"Synology 登入狀態: {auth is not None}")

    if not auth:
        logging.error("Synology 登入失敗，請檢查帳號密碼或網路連線")
        return jsonify({"error": "Synology 登入失敗"}), 500
    logging.info("Synology 登入成功")
    service = get_service(creds)
    google_album_id = get_or_create_album(service, album_name)

    update_people_list(auth)

    delete_all_photos_from_album(google_album_id)
    result = run_sync(auth, creds, person_id, album_id, num_photos, google_album_id, token)

    # new_batch = create_new_batch(auth)
    # if new_batch:
    #     logging.info(f"Batch {new_batch.batch_number} created by {new_batch.uploaded_by}")
    # else:
    #     logging.warning("Batch creation failed unexpectedly.")

    logging.info(f"同步完成，共上傳 {result['uploaded']} 張照片，耗時 {round(time.time() - start_time, 2)} 秒")

    return jsonify({
        "uploaded_photos": result['uploaded'],
        "time_spent": round(time.time() - start_time, 2),
        "sync_report": result['messages'],
        "token": token
    })

def run_sync(auth, creds, person_id, album_id, num_photos, google_album_id, token):
    token_map.clear()
    report = get_photos_upload_to_album(auth, person_id, album_id, num_photos, token)
    if not report:
        logging.error("⚠️ 獲取照片上傳報告失敗，請檢查 Synology 服務是否正常")
        return {"uploaded": 0, "messages": ["無法獲取照片上傳報告"]}
    logging.info(f"獲取到 {len(report.get('photos', []))} 張照片，準備下載和上傳到 Google 相簿")
    for photo in report.get("photos", []):
        download_queue.put(photo)

    def download_worker():
        while True:
            try:
                p = download_queue.get(timeout=2)
            except queue.Empty:
                break
            saved_path = os.path.join(DOWNLOAD_DIR, p['filename'])
            download_photo(auth, p, save_path=saved_path)
            photo_queue.put(p['filename'])

    def upload_worker():
        while True:
            try:
                filename = photo_queue.get(timeout=2)
            except queue.Empty:
                break
            saved_path = os.path.join(DOWNLOAD_DIR, filename)
            token_map[filename] = upload_photo_bytes(creds, saved_path)
            photo_queue.task_done()

    downloaders = [threading.Thread(target=download_worker) for _ in range(NUM_DOWNLOAD_THREADS)]
    uploaders = [threading.Thread(target=upload_worker) for _ in range(NUM_UPLOAD_THREADS)]
    [t.start() for t in downloaders]
    [t.start() for t in uploaders]
    [t.join() for t in downloaders]
    photo_queue.join()
    [t.join() for t in uploaders]

    add_photos_to_album(creds, google_album_id, token_map)
    return {
        "uploaded": len(token_map),
        "messages": report['messages']
    }



