from flask import Blueprint, request, jsonify
import requests
from services.line_service import handle_webhook
import traceback
import logging
from config.config import Config
from flask import session
from linebot import LineBotApi
from linebot.models import TextSendMessage

# 設定 Line Bot API
line_bot_api = LineBotApi(Config.LINE_CHANNEL_ACCESS_TOKEN)

logging.basicConfig(filename="error.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

line_bp = Blueprint("line_bp", __name__)
user_sessions = {}
import secrets

def generate_token(length=32):
    """產生指定長度的安全隨機 token"""
    return secrets.token_hex(length // 2)

@line_bp.route("/webhook", methods=["GET", "POST"])
def webhook():
    try:
        caller = request.headers.get("X-Caller")

        if caller == "album":
            return jsonify({"message": "這是從 /album 呼叫的 webhook"})
        else:
            logging.error("Received webhook request")
            data = request.get_json(force=True)  # 強制解析 json，避免拿到字串

            if not data:
                return jsonify({"error": "Invalid JSON"}), 400
            logging.error(f"Webhook result: {data}")
            event = data["events"][0]
            uid = event["source"]["userId"]
            token = generate_token()
            if uid:
                user_sessions[token] = uid

            result = handle_webhook(data, token)
            return jsonify(result), 200
    except Exception as e:
        logging.error(f"Error in /api/webhook: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@line_bp.route("/notify", methods=["POST"])
def notify():
    try:
        logging.error(f"Received notify request: {request.json}")
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        data = request.get_json(force=True)
        if not data or "message" not in data or "token" not in data:
            return jsonify({"error": "Invalid JSON or missing 'message' or 'token'"}), 400
        message = data["message"]
        token = data["token"]
        user_id = user_sessions.get(token)
        logging.error(f"User ID from token {token}: {user_id}")
        if not user_id:
            logging.error("User ID not found in session")
            return jsonify({"error": "User ID not found in session"}), 400

        payload = {
            "to": user_id,
            "messages": [{"type": "text", "text": message}]
        }
        headers = {
            "Authorization": f"Bearer {Config.LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        # 這裡改成 push URL
        response = requests.post("https://api.line.me/v2/bot/message/push", json=payload, headers=headers)
        logging.error(f"Notify response: {response.status_code}, {response.text}")
        if response.status_code != 200:
            logging.error(f"Failed to send message: {response.status_code}, {response.text}")
            return jsonify({"error": "Failed to send message"}), 500
        # 如果有上傳照片的需求，這裡可以處理
        response.raise_for_status()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logging.error(f"Error in /notify: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@line_bp.route("/album", methods=["POST"])
def get_albums():
    data = request.get_json(force=True)
    if not data or "token" not in data:
        return jsonify({"error": "Invalid JSON or missing 'token'"}), 400

    token = data["token"]
    albums = data.get("albums", [])
    user_id = user_sessions.get(token)

    if not user_id:
        logging.error("User ID not found in session")
        return jsonify({"error": "User ID not found in session"}), 400

    logging.error(f"User ID from token {token}: {user_id}")
    logging.error(f"Retrieved {albums} albums")

    text = f"已取得相簿：\n" + "\n".join(albums)
    logging.error(f"Sending albums to user {user_id}: {text}")

    try:
        line_bot_api.push_message(user_id, TextSendMessage(text=text))
    except Exception as e:
        logging.exception(f"Failed to send LINE message: {e}")
        return jsonify({"error": "Failed to send LINE message"}), 500

    return jsonify({"albums": albums})
