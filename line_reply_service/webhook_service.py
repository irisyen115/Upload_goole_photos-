from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()
ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
PUSH_URL = os.getenv("LINE_PUSH_URL")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

def push_message(user_id, message):
    os.makedirs("sessions", exist_ok=True)
    quick_reply = {
        "items": [
            {
                "type": "action",
                "action": {
                    "type": "message",
                    "label": "我要上傳照片",
                    "text": "我要上傳照片"
                }
            },
            {
                "type": "action",
                "action": {
                    "type": "message",
                    "label": "不需要上傳",
                    "text": "不需要上傳"
                }
            },
            {
                "type": "action",
                "action": {
                    "type": "message",
                    "label": "使用自訂參數",
                    "text": "使用自訂參數"
                }
            }
        ]
    }

    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message,
                "quickReply": quick_reply
            }
        ]
    }
    response = requests.post(PUSH_URL, headers=headers, json=payload)
    with open(f"sessions/{user_id}.json", "w", encoding="utf-8") as f:
        json.dump({"last_action": "asked_album_change"}, f)

    print(f"[{user_id}] 發送結果：{response.status_code} {response.text}")

def push_to_all_users(user_list_path="user_ids.txt", message="這是自動發送的訊息，祝你今天愉快！"):
    if not os.path.exists(user_list_path):
        print(f"找不到 {user_list_path}")
        return

    with open(user_list_path, "r", encoding="utf-8") as f:
        user_ids = [line.strip() for line in f if line.strip()]

    for user_id in user_ids:
        push_message(user_id, message)

if __name__ == "__main__":
    user_list_path = '/app/user_ids.txt'
    message = '已經到了同步相簿的時間了喔，請問可有需要更換相簿照片'
    push_to_all_users(user_list_path, message)
