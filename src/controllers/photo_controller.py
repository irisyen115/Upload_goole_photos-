from flask import request, jsonify, session, Blueprint
from models.database import SessionLocal
from service.photo_service import get_upload_records_service
from lib.google import authenticate

photo_db = Blueprint('photo', __name__)
import logging

logging.basicConfig(filename="error.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

@photo_db.route('/upload_records', methods=['GET'])
def get_upload_records():
    db = SessionLocal()
    person_id = request.args.get('personID') or session.get('person_id')
    creds = authenticate()
    logging.error("person_id: %s", person_id)

    try:
        result = get_upload_records_service(db, person_id, creds)
        return jsonify(result)
    finally:
        db.close()
