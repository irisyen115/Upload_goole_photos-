from models import Photo, ExistPerson, PhotoBlacklist
from sqlalchemy.sql import func
from config.config import Config
from service.user_service import get_user_info_service

def get_upload_records_service(db, person_id, creds):
    # 可依需求選擇是否啟用 person_id 過濾
    query = (
        db.query(Photo)
        .join(ExistPerson, ExistPerson.photo_id == Photo.item_id)
        .filter(~Photo.item_id.in_(db.query(PhotoBlacklist.photo_id)))
        # .filter(ExistPerson.person_id == person_id)
        .order_by(func.random())
    )

    records = query.all()
    user_info = get_user_info_service(creds)

    if "name" not in user_info:
        raise ValueError(f"取得使用者資訊失敗: {user_info.get('error', '未知錯誤')}")

    result = [{
        "filename": photo.filename,
        "photo_id": photo.item_id,
        "url": Config.ALBUM_URL,
        "name": user_info["name"],
    } for photo in records]

    return result
