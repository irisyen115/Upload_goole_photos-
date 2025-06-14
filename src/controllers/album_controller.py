from flask import Blueprint, request, jsonify
from lib.google import (
    get_service,
    get_google_album_list,
    authenticate
)
import logging
import requests
from config.config import Config

logging.basicConfig(filename="error.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

album_db = Blueprint('album_db', __name__)
@album_db.route('/list_albums', methods=['POST'])
def get_albums():
    """取得 Google Photos 相簿列表"""
    logging.error("Received request to list albums")
    token = request.args.get('token')
    if not token:
        return jsonify({"error": "Token is required"}), 400
    logging.error(f"Token provided: {token}")
    creds = authenticate()
    if not creds:
        return jsonify({"error": "Credentials are required"}), 400

    service = get_service(creds)
    if not service:
        return jsonify({"error": "Failed to create Google Photos service"}), 500

    try:
        albums = get_google_album_list(service, creds)
        album_titles = [album['title'] for album in albums if 'title' in album]

        requests.post(f"{Config.SERVER_URL}/api/line/album", json={
            "albums": album_titles,
            "token": token
        })
        logging.error(f"Albums fetched: {album_titles}")
        return jsonify(album_titles), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500