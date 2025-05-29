from lib.synlogy import list_all_photos_by_person, list_all_photos_by_album
from models.database import SessionLocal
from models.photo import Photo
from models.person import Person
from models.album import Album

def get_latest_photo(person_id, album_id):
    db = SessionLocal()
    if person_id:
        latest_photo = (
            db.query(Photo)
            .join(Person, Person.photo_id == Photo.item_id)
            .filter(Person.person_id == person_id)
            .order_by(Photo.shooting_time.desc())
            .first()
        )
        return latest_photo
    else:
        latest_photo = (
            db.query(Photo)
            .join(Album, Album.photo_id == Photo.item_id)
            .filter(Album.album_id == album_id)
            .order_by(Photo.shooting_time.desc())
            .first()
        )
        return latest_photo