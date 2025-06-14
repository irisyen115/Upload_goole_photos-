from flask import Blueprint, request, jsonify
from models import UploadBatch, ExistPerson
from models.database import SessionLocal

batch_db = Blueprint('batch_db', __name__)

@batch_db.route('/upload_batches', methods=['GET'])
def get_upload_batches():
    db = SessionLocal()
    try:
        # 查詢 ExistPerson 資料數與最新上傳時間
        count = db.query(ExistPerson).count()
        latest_photo = db.query(ExistPerson).order_by(ExistPerson.uploaded_at.desc()).first()

        if latest_photo:
            upload_time = latest_photo.uploaded_at.isoformat()
        else:
            upload_time = None

        # 查詢最新的 UploadBatch
        new_batches = db.query(UploadBatch).order_by(UploadBatch.id.desc()).all()

        if not new_batches:
            return jsonify({"error": "No upload batches found"}), 404

        result = [{
            "batch_number": new_batch.batch_number,
            "name": new_batch.uploaded_by,
            "upload_person": new_batch.upload_person,
            "num_photos": new_batch.count,
            "upload_time": new_batch.upload_time,
        } for new_batch in new_batches]

        return jsonify(result)
    finally:
        db.close()
