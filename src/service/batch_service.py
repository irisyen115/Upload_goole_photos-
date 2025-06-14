from models import UploadBatch, ExistPerson
from models.database import SessionLocal
from service.user_service import get_user_info_service
from lib.google import authenticate
from lib.synlogy import get_person, login
import logging

logging.basicConfig(filename="error.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

def get_next_batch_number(db, username):
    last_batch = db.query(UploadBatch).filter(UploadBatch.uploaded_by == username)\
                                        .order_by(UploadBatch.batch_number.desc())\
                                        .first()
    if last_batch is None:
        next_batch_num = 1
    else:
        next_batch_num = last_batch.batch_number + 1
    return next_batch_num

def create_new_batch(auth):
    """
    建立新的上傳批次，並返回 UploadBatch 物件
    :param auth: Synology 認證物件
    :return: UploadBatch 物件
    """
    db = SessionLocal()
    try:
        creds = authenticate()
        user_info = get_user_info_service(creds)
        user_name = user_info.get('name')
        if not user_name:
            raise ValueError("使用者名稱為空")

        count = db.query(ExistPerson).count()
        latest_photo = db.query(ExistPerson).order_by(ExistPerson.uploaded_at.desc()).first()

        if latest_photo is None:
            logging.warning("資料庫中無任何 ExistPerson 紀錄，將使用 '所有人' 作為上傳人")
            person_name = '所有人'
            upload_time = None
        else:
            if latest_photo.person_id is None:
                logging.warning("最新照片的 person_id 為 None，將使用 '所有人' 作為上傳人")
                person_name = '所有人'
            else:
                logging.info(f"最新照片的 person_id: {latest_photo.person_id}")
                person_name = get_person_name(auth, latest_photo.person_id)

        upload_time = latest_photo.uploaded_at.isoformat()

        next_batch_num = get_next_batch_number(db, user_name)
        new_batch = UploadBatch(uploaded_by=user_name, batch_number=next_batch_num, count=count, upload_person=person_name, upload_time=upload_time)
        logging.info(f"建立新的 Batch: {next_batch_num} 由 {user_name} 上傳，共 {count} 張照片")

        db.add(new_batch)
        db.commit()
        db.refresh(new_batch)
        return new_batch
    except Exception as e:
        db.rollback()
        logging.error(f"建立 Batch 時發生錯誤: {e}")
        raise
    finally:
        db.close()

def get_person_name(auth, person_id):
    try:
        person_data = get_person(auth, person_id)
        logging.info(f"取得 Person 資料: {person_data}")

        # 不檢查 'data'，改檢查 'list'
        if not person_data or 'list' not in person_data:
            raise ValueError("回傳資料缺少 'list' 欄位")

        if not person_data['list']:
            raise ValueError("'list' 是空的")

        name = person_data['list'][0].get('name')
        if not name:
            raise ValueError("回傳資料中 'name' 為空或不存在")

        return name

    except Exception as e:
        logging.error(f"取得 Person 名稱失敗: {e}")
        return '未知'
