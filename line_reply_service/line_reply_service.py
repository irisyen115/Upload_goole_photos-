from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
import json
import subprocess
import logging
import threading
from models.database import init_db, db
from models.line_binding_user import LineBindingUser
import traceback
from models.users import User
from linebot.models import FlexSendMessage, MessageAction

logging.basicConfig(filename='app.log', level=logging.INFO)

load_dotenv()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
init_db(app)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"
IRIS_DS_SERVER_URL = 'https://irisyen115.synology.me'

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
}

@app.route("/api/webhook", methods=["POST"])
def reply():
    data = request.json
    session_data = {}

    try:
        binding = LineBindingUser.query.with_entities(LineBindingUser.line_id).all()
        bound_users = {user.line_id for user in binding}
        event = data["events"][0]
        reply_token = event["replyToken"]
        message_text = event["message"]["text"]
        uid = event["source"]["userId"]
        reply_text = ""

        session_path = f"sessions/{uid}.json"

        if os.path.exists(session_path):
            with open(session_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)

        if event["type"] == "follow":
            if uid not in bound_users:
                send_bind_button(reply_token)
            else:
                send_already_bound_msg(reply_token)
            return jsonify({"status": "follow handled"}), 200

        elif event["type"] == "message":
            message_text = event["message"].get("text", "")
            is_bound = LineBindingUser.query.filter_by(line_id=uid).first() is not None

            if is_bound:
                save_user_id(uid)
            if message_text == "綁定":
                if uid not in bound_users:
                    bound_users.add(uid)
                    send_bind_url(reply_token, uid)
                else:
                    send_already_bound_msg(reply_token)
                return jsonify({"status": "binding handled"}), 200

        if session_data:
            if session_data.get("last_action") == "asked_album_change":
                reply_text = handle_message(uid, message_text, session_data)
            payload = build_payload(reply_token, reply_text)
        else:
            reply_text = "請先輸入綁定"
            payload = {
                "replyToken": reply_token,
                "messages": [{"type": "text", "text": reply_text}]
            }

        with open(session_path, "w", encoding="utf-8") as f:
            json.dump(session_data, f)

        r = requests.post(LINE_REPLY_URL, json=payload, headers=headers)

        r.raise_for_status()

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print("Webhook Error:", e)
        traceback.print_exc()
        if 'r' in locals():
            app.logger.error(f"LINE API 錯誤狀態碼: {r.status_code}")
            app.logger.error(f"LINE API 錯誤內容: {r.text}")
        return "Internal Server Error", 500


def save_user_id(uid, user_ids_file='user_ids.txt'):
    if os.path.exists(user_ids_file):
        with open(user_ids_file, 'r', encoding='utf-8') as f:
            existing_ids = set(line.strip() for line in f if line.strip())
    else:
        existing_ids = set()

    if uid not in existing_ids:
        with open(user_ids_file, 'a', encoding='utf-8') as f:
            f.write(uid + '\n')
        print(f"新增 user_id: {uid}")
    else:
        print(f"user_id {uid} 已存在，不重複寫入")

def build_payload(reply_token, reply_text):
    if isinstance(reply_text, FlexSendMessage):
        messages = [reply_text.as_json_dict()]
    elif isinstance(reply_text, dict) and "type" in reply_text:
        messages = [reply_text]
    elif isinstance(reply_text, list):
        messages = [
            msg.as_json_dict() if isinstance(msg, FlexSendMessage) else msg
            for msg in reply_text
        ]
    else:
        messages = [{"type": "text", "text": reply_text}]

    return {
        "replyToken": reply_token,
        "messages": messages
    }

user_states = {}

def handle_message(user_id, message_text, session_data):
    try:
        state = user_states.get(user_id, {})
        faces = []

        people_list_path = os.path.join("/app/people_list", "people_list.json")
        if os.path.exists(people_list_path):
            with open(people_list_path, "r", encoding="utf-8") as f:
                faces = json.load(f)

        if message_text == "使用自訂參數":
            user_states[user_id] = {"step": "ask_person"}
            bubbles = []
            for face in faces:
                bubbles.append({
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": face["name"], "weight": "bold", "size": "xl"},
                            {"type": "button", "style": "primary", "action": {
                                "type": "message",
                                "label": "選擇",
                                "text": f"上傳 {face['ID']}"
                            }},
                        ]
                    }
                })
            carousel = {"type": "carousel", "contents": bubbles}
            return FlexSendMessage(alt_text="請選擇人物上傳照片", contents=carousel)

        elif message_text == "我要上傳照片":
            user_states[user_id] = {
                "step": "ask_person",
                "album_name": "default",
                "num_photos": 50
            }
            bubbles = []
            for face in faces:
                bubbles.append({
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents":  [
                        {"type": "text", "text": face["name"], "weight": "bold", "size": "xl"},
                        # {
                        #     "type": "image",
                        #     "url": face['img'],
                        #     "aspectRatio": "1:1",
                        #     "size": "full",
                        #     "aspectMode": "fit",
                        #     "gravity": "center"
                        # },
                        {
                            "type": "button",
                            "style": "primary",
                            "action": {
                                "type": "message",
                                "label": "選擇",
                                "text": f"上傳 {face['ID']}"
                            }
                        }
                    ]
                    }
                })
            carousel = {"type": "carousel", "contents": bubbles}
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

                    threads = []
                    for _ in range(16):
                        t = threading.Thread(
                            target=do_upload,
                            args=(state["person_id"], state["album_name"], state["num_photos"], user_id, session_data)
                        )

                        t.start()
                        threads.append(t)

                    for t in threads:
                        t.join()
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
            state["num_photos"] = int(message_text)
            state["step"] = "uploading"
            user_states[user_id] = state
            threading.Thread(
                target=do_upload,
                args=(state["person_id"], state["album_name"], state["num_photos"], user_id, session_data)
            ).start()
            return f"✅ 收到資訊！正在上傳 {state['num_photos']} 張照片到相簿 '{state['album_name']}'，請稍候..."

        elif state.get("step") == "uploading":
            return "🚫 照片正在上傳中，請稍候完成再繼續操作喔！"

        else:
            return "請輸入「我要上傳照片」來開始相簿上傳流程。"

    except Exception as e:
        logging.error(e)
        return "⚠️ 發生錯誤，請稍後再試。"

def do_upload(person_id, album_name, num_photos, user_id, session_data):
    try:
        last_upload = session_data.get("last_upload")
        current_upload = f"{person_id}_{album_name}_{num_photos}"

        if last_upload == current_upload:
            logging.warning(f"🚫 重複上傳阻止：{current_upload}")
            return

        session_data["last_upload"] = current_upload

        payload = {
            "personID": person_id,
            "albumID": None,
            "albumName": album_name,
            "numPhotos": num_photos
        }

        response = requests.post("http://google-photos:5050/sync_photos", json=payload)

        user_states.pop(user_id, None)
        session_data["last_action"] = None
        logging.info(f"User {user_states} has completed the upload process.")
        session_path = f"sessions/{user_id}.json"
        with open(session_path, "w") as f:
            json.dump(session_data, f)

        logging.info(f"✅ User {user_id} has completed the upload process.")
        print(response.json())
    except Exception as e:
        logging.error(f"❌ Upload failed: {e}")

def send_bind_button(reply_token, uid):
    bind_url = f"{IRIS_DS_SERVER_URL}/Line-login?uid={uid}"

    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "template",
                "altText": "請點擊以下按鈕進行綁定",
                "template": {
                    "type": "buttons",
                    "title": "帳號綁定",
                    "text": "請點擊下方按鈕以綁定您的帳號",
                    "actions": [
                        {
                            "type": "uri",
                            "label": "前往綁定",
                            "uri": bind_url
                        }
                    ]
                }
            }
        ]
    }

    requests.post(LINE_REPLY_URL, json=payload, headers=headers)

def send_bind_url(reply_token, uid):
    login_url = f"{IRIS_DS_SERVER_URL}/Line-login?uid={uid}"
    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": f"請點擊以下網址進行綁定：\n{login_url}"
            }
        ]
    }
    requests.post(LINE_REPLY_URL, json=payload, headers=headers)

def send_already_bound_msg(reply_token):
    payload = {
        "replyToken": reply_token,
        "messages": [
            {"type": "text", "text": "您已經綁定過帳號，謝謝！"}
        ]
    }
    requests.post(LINE_REPLY_URL, json=payload, headers=headers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
