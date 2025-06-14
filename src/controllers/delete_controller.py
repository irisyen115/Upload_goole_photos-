from flask import Blueprint, request, jsonify
from service.delete_service import handle_delete_photo
import logging

logging.basicConfig(filename="error.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

delete_bp = Blueprint('delete', __name__)

@delete_bp.route('/delete_photo', methods=['POST'])
def delete_photo():
    data = request.get_json()
    filenames = data.get("filenames")
    album_name = data.get("album_name")

    if not filenames or not album_name:
        return jsonify({"error": "請提供 filenames 和 album_name"}), 400

    try:
        result = handle_delete_photo(filenames, album_name)
        return jsonify(result), 200
    except Exception as e:
        logging.error("刪除失敗: %s", e)
        return jsonify({"error": str(e)}), 500
