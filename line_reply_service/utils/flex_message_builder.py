# utils/flex_message_builder.py
from linebot.models import FlexSendMessage
import requests
import os
from config.config import Config
import logging
logging.basicConfig(filename="error.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {Config.LINE_CHANNEL_ACCESS_TOKEN}"
}

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

def build_face_bubbles(faces):
    bubbles = []
    for face in faces:
        bubbles.append({
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "lg",
                "contents": [
                    {
                        "type": "text",
                        "text": face["name"],
                        "weight": "bold",
                        "size": "xl",
                        "align": "center"
                    },
                    {
                        "type": "image",
                        "url": face["img"],
                        "aspectRatio": "1:1",
                        "size": "full",
                        "aspectMode": "cover",
                        "gravity": "center"
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "margin": "lg",
                        "action": {
                            "type": "message",
                            "label": "選擇",
                            "text": f"上傳 {face['ID']}"
                        }
                    }
                ]
            }
        })
    return bubbles

def send_bind_url(reply_token, uid):
    login_url = f"{Config.SERVER_URL}/Line-login?uid={uid}"
    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": f"請點擊以下網址進行綁定：\n{login_url}"
            }
        ]
    }
    requests.post(Config.LINE_REPLY_URL, json=payload, headers=headers)

def send_flex_login(auth_url):
    bubbles = []
    bubbles.append({
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "lg",
            "contents": [
            {
                "type": "text",
                "text": "🟡 尚未登入 Google",
                "weight": "bold",
                "size": "lg"
            },
            {
                "type": "text",
                "text": "請點擊以下按鈕登入：",
                "size": "md"
            },
            {
                "type": "button",
                "style": "primary",
                "action": {
                "type": "uri",
                "label": "登入 Google",
                "uri": auth_url
                }
            }
            ]
        }
        }
        )
    carousel = {"type": "carousel", "contents": bubbles}
    return FlexSendMessage(alt_text="請授權 google 帳戶", contents=carousel)

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
def send_already_bound_msg(reply_token):
    payload = {
        "replyToken": reply_token,
        "messages": [
            {"type": "text", "text": "您已經綁定過帳號，謝謝！"}
        ]
    }
    requests.post(Config.LINE_REPLY_URL, json=payload, headers=headers)

def send_bind_button(reply_token, uid):
    bind_url = f"{Config.SERVER_URL}/Line-login?uid={uid}"

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

    requests.post(Config.LINE_REPLY_URL, json=payload, headers=headers)