from flask import Flask, request, jsonify, Blueprint
from models.photo_blacklist import PhotoBlacklist
from models.photo import Photo
from sqlalchemy.sql import func
from models.database import SessionLocal
from config.config import Config

black_db = Blueprint('black', __name__)

@black_db.route('/blacklist_photo', methods=['POST'])
def blacklist_photo():
    data = request.get_json()
    photo_id = data.get('photo_id')
    reason = data.get('reason', '')

    if not photo_id:
        return jsonify({"error": "photo_id is required"}), 400

    db = SessionLocal()

    # 正確查詢方式：使用 session 來查
    existing = db.query(PhotoBlacklist).filter_by(photo_id=photo_id).first()
    if existing:
        db.close()
        return jsonify({"error": "photo_id already in blacklist"}), 400

    # 新增黑名單紀錄
    new_entry = PhotoBlacklist(photo_id=photo_id, reason=reason)
    db.add(new_entry)
    db.commit()
    db.close()

    return jsonify({"message": "Photo blacklisted successfully"}), 200

@black_db.route('/blacklist', methods=['GET'])
def get_blacklist():
    db = SessionLocal()
    try:
        # records = db.query(PhotoBlacklist).all()
        query = (
            db.query(Photo)
            .join(PhotoBlacklist, PhotoBlacklist.photo_id == Photo.item_id)
            # .filter(~Photo.item_id.in_(db.query(PhotoBlacklist.photo_id)))
            # .filter(ExistPerson.person_id == person_id)
            .order_by(func.random())
        )

        records = query.all()
        result = [{"photo_id": record.item_id, "url": Config.ALBUM_URL, "filename": record.filename} for record in records]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
