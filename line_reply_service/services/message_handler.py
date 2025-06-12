# services/message_handler.py
import os
import json
import threading
from linebot.models import FlexSendMessage
from utils.flex_message_builder import build_face_bubbles, send_flex_login
from services.upload_service import do_upload
from config.config import Config
import logging
import requests

session = requests.Session()

logging.basicConfig(filename="error.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

user_states = {}

def get_people_list(session):
    people_list_path = os.path.join("/app/people_list", "people_list.json")
    faces = []
    if not os.path.exists("/app/people_list"):
        try:
            os.makedirs("/app/people_list")
        except Exception as e:
            logging.error(f"建立目錄 /app/people_list 時發生錯誤: {e}")
            return []
    logging.error(f"people_list_path: {people_list_path}")

    if os.path.exists(people_list_path):
        try:
            with open(people_list_path, "r", encoding="utf-8") as f:
                faces = json.load(f)
        except Exception as e:
            logging.error(f"讀取 people_list.json 時發生錯誤: {e}")
    else:
        logging.error("people_list.json 不存在，嘗試從遠端服務獲取")
        try:
            logging.error("people_list.json 不存在，嘗試從遠端服務獲取")
            response = session.get(f"{Config.SERVER_URL}/api/upload/update_people", verify=False, timeout=10)
            if response.status_code == 200:
                try:
                    faces = response.json()
                    with open(people_list_path, "w", encoding="utf-8") as f:
                        json.dump(faces, f, ensure_ascii=False, indent=2)
                    logging.info(f"成功從遠端服務獲取 {len(faces)} 人物資料")
                except Exception as e:
                    logging.error(f"解析 JSON 時發生錯誤: {e}")
                    return []

                if not isinstance(faces, list):
                    logging.error(f"⚠️ 回傳格式錯誤，預期為 list，但實際為 {type(faces)}，內容為: {faces}")

                    return []
            else:
                logging.warning(f"請求 update_people 失敗，HTTP {response.status_code}")
        except requests.RequestException as e:
            logging.error(f"連接遠端服務時發生錯誤: {e}")

    return faces

people_cache = []
cache_lock = threading.Lock()

def preload_faces():
    global people_cache
    new_faces = get_people_list(session)
    with cache_lock:
        people_cache = new_faces

# 服務啟動時先非同步預載
threading.Thread(target=preload_faces).start()

def get_cached_faces():
    global people_cache
    with cache_lock:
        cache_empty = not people_cache
    if cache_empty:
        new_faces = get_people_list(session)
        with cache_lock:
            people_cache = new_faces
    with cache_lock:
        return people_cache.copy()

def handle_message(user_id, message_text, session, session_data):
    try:
        state = user_states.get(user_id, {})
        people_list_path = os.path.join("/app/people_list", "people_list.json")
        if not os.path.exists(people_list_path):
            threading.Thread(target=preload_faces).start()
            return "⚠️ 人物列表尚未載入，請稍後再試。"

        faces = get_cached_faces()
        if not faces:
            return "⚠️ 無法取得人物列表，請稍後再試。"

        if message_text == "使用自訂參數":
            user_states[user_id] = {"step": "ask_person"}
            carousel = {"type": "carousel", "contents": build_face_bubbles(faces)}
            return FlexSendMessage(alt_text="請選擇人物上傳照片", contents=carousel)

        elif message_text == "我要上傳照片":
            logging.error(f"faces type: {type(faces)}, value: {faces}")
            faces = get_cached_faces()
            if not faces:
                logging.error("⚠️ faces is empty after get_cached_faces")
                return "⚠️ 無法取得人物列表，請稍後再試。"
            logging.error(f"faces length: {len(faces)}")
            if not isinstance(faces, list):
                logging.error(f"⚠️ faces is not a list, type: {type(faces)}")
                return "⚠️ 無法取得人物列表，請稍後再試。"
            logging.error(f"faces: {faces}")

            user_states[user_id] = {
                "step": "ask_person",
                "album_name": "default",
                "num_photos": 5
            }
            logging.error(1)

            if faces is None or not isinstance(faces, list):
                logging.error("⚠️ faces is None or not a list")
                return "⚠️ 無法取得人物列表，請稍後再試。"
            carousel = {"type": "carousel", "contents": build_face_bubbles(faces)}
            logging.error(12)


            for i, bubble in enumerate(carousel.get("contents", [])):
                logging.error(i)

                contents = bubble.get("body", {}).get("contents", [])
                for j, content in enumerate(contents):
                    logging.error(j)

                    if content is None:
                        logging.error(f"Null element found in contents[{i}].body.contents[{j}]")

            return FlexSendMessage(alt_text="請選擇人物上傳照片", contents=carousel)
        elif state.get("step") == "ask_person":
            if message_text.startswith("上傳 "):
                person_id = message_text.split("上傳 ")[1].strip()
                if not person_id.isdigit():
                    return "❌ 請提供有效的人物 ID，例如：22492"

                state["person_id"] = person_id
                if "album_name" in state and "num_photos" in state:
                    state["step"] = "uploading"
                    user_states[user_id] = state
                    threading.Thread(
                        target=do_upload,
                        args=(state["person_id"], state["album_name"], state["num_photos"], user_id, session, session_data, user_states)
                    ).start()
                    return f"✅ 收到資訊！正在上傳 {state['num_photos']} 張照片到相簿 '{state['album_name']}'，請稍候..."
                else:
                    state["step"] = "ask_name"
                    user_states[user_id] = state
                    return "🔗 請提供 Google Photos 相簿名："
            else:
                return "請點選選單上的「選擇」按鈕選擇人物。"

        elif state.get("step") == "ask_name":
            state["album_name"] = message_text
            state["step"] = "ask_count"
            user_states[user_id] = state
            return "🔢 請提供要上傳的照片數量（例如：10）："

        elif state.get("step") == "ask_count":
            if not message_text.isdigit():
                return "❌ 請輸入正確的數字"
            num_photos = int(message_text)

            state["num_photos"] = num_photos
            state["step"] = "uploading"
            user_states[user_id] = state

            threading.Thread(
                target=do_upload,
                args=(state["person_id"], state["album_name"], state["num_photos"], user_id, session, session_data, user_states)
            ).start()
            return f"✅ 收到資訊！正在上傳 {state['num_photos']} 張照片到相簿 '{state['album_name']}'，請稍候..."

        else:
            return "請輸入「我要上傳照片」來開始相簿上傳流程。"

    except Exception as e:
        logging.error(e)
        return "⚠️ 發生錯誤，請稍後再試。"

