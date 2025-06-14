import os
import json
import requests
from models.line_binding_user import LineBindingUser
from services.message_handler import handle_message
from utils.flex_message_builder import (
    build_payload, send_bind_button, send_already_bound_msg, send_bind_url, save_user_id
)
from services.session_manager import load_session, save_session
from config.config import Config
import logging
logging.basicConfig(filename="error.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

def handle_webhook(data, token):
    session = requests.session()
    session_data = {}
    if "events" not in data or not data["events"]:
        logging.warning("Webhook 事件為空，略過處理")
        return {"status": "no events"}

    event = data["events"][0]
    reply_token = event["replyToken"]
    uid = event["source"]["userId"]
    message_text = event.get("message", {}).get("text", "")

    session_data = load_session(uid)
    # 取得綁定資訊
    bound_users = {user.line_id for user in LineBindingUser.query.with_entities(LineBindingUser.line_id).all()}
    save_user_id(uid)

    if event["type"] == "follow":
        if uid not in bound_users:
            send_bind_button(reply_token, uid)
        else:
            send_already_bound_msg(reply_token)
        return {"status": "follow handled"}

    elif event["type"] == "message":
        if message_text == "綁定":
            is_bound = LineBindingUser.query.filter_by(line_id=uid).first() is not None
            if not is_bound:
                send_bind_url(reply_token, uid)
            else:
                send_already_bound_msg(reply_token)
            return {"status": "binding handled"}

        is_bound = LineBindingUser.query.filter_by(line_id=uid).first() is not None
        if is_bound:
            reply_text = handle_message(uid, message_text, session, session_data, token)
            payload = build_payload(reply_token, reply_text)
        else:
            payload = {
                "replyToken": reply_token,
                "messages": [{"type": "text", "text": "請先輸入綁定"}]
            }

        r = requests.post(Config.LINE_REPLY_URL, json=payload, headers=Config.headers)
        r.raise_for_status()

        save_session(uid, session_data)

        return {"status": "success"}

    return {"status": "ignored"}
