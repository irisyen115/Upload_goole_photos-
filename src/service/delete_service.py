from lib.google import (
    get_service,
    authenticate,
    get_or_create_album,
    list_media_items_in_album,
    find_media_item_ids_by_filenames,
    remove_all_items_from_album
)

from models.database import SessionLocal
from models import Photo, ExistPerson


def handle_delete_photo(filenames, album_name):
    creds = authenticate()
    if not creds or not creds.valid:
        raise Exception("尚未授權或憑證失效")

    service = get_service(creds)
    google_album_id = get_or_create_album(service, album_name=album_name)
    if not google_album_id:
        raise Exception("無法取得 Google 相簿 ID")

    media_items = list_media_items_in_album(service, google_album_id)
    media_item_ids = find_media_item_ids_by_filenames(media_items, filenames)

    remove_all_items_from_album(service, google_album_id, media_item_ids)

    db = SessionLocal()
    try:
        photos_to_delete = db.query(Photo).filter(Photo.filename.in_(filenames)).all()
        photo_ids = [p.item_id for p in photos_to_delete]

        db.query(ExistPerson).filter(
            ExistPerson.photo_id.in_(photo_ids)
        ).delete(synchronize_session=False)

        db.commit()
    finally:
        db.close()

    return {
        "status": "success",
        "deleted_filenames": filenames
    }
