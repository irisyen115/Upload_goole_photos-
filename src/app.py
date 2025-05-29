from flask import Flask, request, jsonify
from lib.synlogy import (
    login, download_photo, list_people
)
from lib.google import (
    authenticate, get_service, get_or_create_album,
    upload_photo_bytes, add_photos_to_album
)
from service.google_service import get_photos_upload_to_album
from delete_photo import delete_all_photos_from_album
from models.database import SessionLocal
from dotenv import load_dotenv
import os
import time
import queue
import threading
import json

app = Flask(__name__)
load_dotenv()
BASE_URL = os.getenv('SYNO_URL')
ACCOUNT = os.getenv('SYNO_ACCOUNT')
PASSWORD = os.getenv('SYNO_PASSWORD')
FID = os.getenv('SYNO_FID')
TIMEZONE = os.getenv('SYNO_TIMEZONE')
DOWNLOAD_DIR = os.getenv('SYNO_DOWNLOAD_DIR', '/app/downloaded_albums/')

NUM_DOWNLOAD_THREADS = 16
NUM_UPLOAD_THREADS = 16

download_queue = queue.Queue()
photo_queue = queue.Queue()
token_map = {}

def download_worker(auth,):
    db = SessionLocal()
    while True:
        try:
            p = download_queue.get(timeout=2)
        except queue.Empty:
            break
        try:
            saved_path = os.path.join(DOWNLOAD_DIR, p['filename'])
            if not photo_queue or not saved_path:
                print(f"⚠️ 略過 {p['filename']}（無儲存路徑）")
                continue
            print(f"🔽 下載中: {p['filename']}")
            download_photo(auth, p, save_path=saved_path)
            photo_queue.put((p['filename']))
        except Exception as e:
            print(f"❌ 下載錯誤: {p['filename']} - {e}")
    db.close()

i = [1]
def upload_worker(creds,):
    while True:
        try:
            filename = photo_queue.get(timeout=2)
        except queue.Empty:
            if all(not t.is_alive() for t in threading.enumerate() if t.name.startswith("Downloader")):
                break
            else:
                continue
        try:
            x = i[0]
            i[0] += 1
            print(f"====== 上傳中 =====, 第 {x} 張照片 ======")
            saved_path = os.path.join(DOWNLOAD_DIR, filename)
            begin = time.time()
            print(f"🔼第 {x} 張， 上傳開始時間: {begin:.2f}")
            upload_token = upload_photo_bytes(creds, saved_path)

            token_map[filename] = upload_token
            end= time.time()
            print(f"🔼第 {x} 張， 上傳結束時間: {end:.2f}, 共耗時: {end-begin:.2f}")
        except Exception as e:
            app.logger.info(f"❌ 上傳錯誤: {filename} - {e}")
        finally:
            photo_queue.task_done()

def initialize_creds():
    auth = login(ACCOUNT, PASSWORD, FID, TIMEZONE)
    creds = authenticate()
    return auth, creds

def sync_all(auth, creds, person_id, album_id, num_photos, google_album_id):
    token_map.clear()
    random_photos = get_photos_upload_to_album(auth, person_id, album_id, num_photos)
    for photo in random_photos:
        download_queue.put(photo)

    downloaders = []
    for i in range(NUM_DOWNLOAD_THREADS):
        t = threading.Thread(target=download_worker, args=(auth,), name=f"Downloader-{i}")
        t.start()
        downloaders.append(t)

    uploaders = []
    for i in range(NUM_UPLOAD_THREADS):
        t = threading.Thread(target=upload_worker, args=(creds,), name=f"Uploader-{i}")
        t.start()
        uploaders.append(t)

    for t in downloaders:
        t.join()

    photo_queue.join()
    for t in uploaders:
        t.join()

    add_photos_to_album(creds, google_album_id, token_map)
    return {
        "uploaded": len(token_map)
    }


@app.route('/sync_photos', methods=['POST'])
def sync_photos():
    data = request.json

    app.logger.info(f"Received data: {data}")
    if not data:
        return jsonify({"error": "請提供有效的 JSON 資料"}), 400
    person_id = data.get("personID")
    album_id = data.get("albumID")
    album_name = data.get("albumName")
    num_photos = data.get("numPhotos")

    if not person_id and not album_id:
        return jsonify({"error": "請提供 personID 或 albumID"}), 400

    try:
        start_time = time.time()
        auth, creds = initialize_creds()
        service = get_service(creds)
        google_album_id = get_or_create_album(service, album_name=album_name)

        people_list_path = os.path.join("/app/people_list", "people_list.json")
        people_list = list_people(auth)

        result_list = []
        for i, person in enumerate(people_list):
            if i == 8:
                print("已獲取前 8 個人臉資料，停止獲取")
                break

            app.logger.error(person['name'])

            result_list.append({
                "name": person['name'],
                "ID": person['id']
            })
        with open(people_list_path, "w", encoding="utf-8") as f:
            json.dump(result_list, f, ensure_ascii=False, indent=2)

        delete_all_photos_from_album(google_album_id)
        result = sync_all(auth, creds, person_id, album_id, num_photos, google_album_id)

        return jsonify({
            "message": "✅ 同步完成",
            "uploaded_photos": result['uploaded'],
            "time_spent": round(time.time() - start_time, 2)
        })
    except Exception as e:
        app.logger.error(f"❌ 同步失敗: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)