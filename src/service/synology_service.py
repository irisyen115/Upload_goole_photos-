from lib.synlogy import list_photos_by_album, list_photos_by_person
from models.photo import Photo
from models.album import Album
from models.person import Person
from models.exist_album import ExistAlbum
from models.exist_person import ExistPerson
from models.photo_blacklist import PhotoBlacklist
from models.database import SessionLocal
from datetime import datetime
from sqlalchemy import func
from config.config import Config
import os

DOWNLOAD_DIR = Config.SYNO_DOWNLOAD_DIR

def list_all_photos_by_album(auth, album_id):
    all_photos = []
    offset = 0
    limit = 100

    while True:
        photos = list_photos_by_album(auth, album_id, offset, limit)
        if not photos:
            break
        all_photos.extend(photos)
        offset += limit

    return all_photos

def list_all_photos_by_person(auth, person_id):
    all_photos = []
    offset = 0
    limit = 100

    while True:
        photos = list_photos_by_person(auth, person_id, offset, limit)
        if not photos:
            break
        all_photos.extend(photos)
        offset += limit

    return all_photos

def save_photos_to_db_with_album(photo_list, album_id):
    db = SessionLocal()
    existing_ids = {
        p.item_id for p in db.query(Photo.item_id).filter(
            Photo.item_id.in_([p['id'] for p in photo_list])
        )
    }

    new_photos = []
    new_album = []

    for p in photo_list:
        if p['id'] not in existing_ids:
            photo = Photo(
                item_id=p['id'],
                filename=p['filename'],
                shooting_time=datetime.fromtimestamp(p['time']),
                saved_path=DOWNLOAD_DIR + p['filename'],
            )
            new_photos.append(photo)
        existing_pair = db.query(Album).filter_by(
            album_id=album_id,
            photo_id=p['id']
        ).first()

        if existing_pair is None:
            album = Album(album_id=album_id, photo_id=p['id'])
            new_album.append(album)
        else:
            album = existing_pair

        print(f"album: {album.album_photo_pair}")

    if new_album:
        db.bulk_save_objects(new_album)
        db.commit()

    if new_photos:
        db.bulk_save_objects(new_photos)
        db.commit()
    else:
        print("⚠️ 沒有新照片需要儲存")

def save_photos_to_db_with_person(photo_list, person_id):
    db = SessionLocal()
    existing_ids = {
        p.item_id for p in db.query(Photo.item_id).filter(
            Photo.item_id.in_([p['id'] for p in photo_list])
        )
    }

    new_photos = []
    new_person = []

    for p in photo_list:
        if p['id'] not in existing_ids:
            photo = Photo(
                item_id=p['id'],
                filename=p['filename'],
                shooting_time=datetime.fromtimestamp(p['time']),
                saved_path=DOWNLOAD_DIR + p['filename'],
            )
            new_photos.append(photo)

        existing_pair = db.query(Person).filter_by(
            person_id=person_id,
            photo_id=p['id']
        ).first()

        if existing_pair is None:
            person = Person(person_id=person_id, photo_id=p['id'])
            new_person.append(person)
        else:
            person = existing_pair

        print(f"person: {person.person_photo_pair}")

    if new_person:
        db.bulk_save_objects(new_person)
        db.commit()
        print(f"✅ 共儲存 {len(new_person)} 張與人臉關聯的照片")

    if new_photos:
        db.bulk_save_objects(new_photos)
        db.commit()
        print(f"✅ 共儲存 {len(new_photos)} 張與相簿關聯的照片")
    else:
        print("⚠️ 沒有新照片需要儲存")

def random_pick_from_person_database(person_id=None, limit=30):
    db = SessionLocal()
    if person_id:
        photos = (
            db.query(Photo)
            .join(Person, Person.photo_id == Photo.item_id)
            .filter(Person.person_id == person_id)
            .order_by(func.random())
            .limit(limit)
            .all()
        )
    else:
        photos = db.query(Photo).order_by(func.random()).limit(limit).all()
    return [{"filename": photo.filename, "id": photo.item_id} for photo in photos]

def randam_pick_from_album_database(album_id=None, limit=30):
    db = SessionLocal()
    if album_id:
        photos = (
            db.query(Photo)
            .join(Album, Album.photo_id == Photo.item_id)
            .filter(Album.album_id == album_id)
            .order_by(func.random())
            .limit(limit)
            .all()
        )
    else:
        photos = db.query(Photo).order_by(func.random()).limit(limit).all()
    return [{"filename": photo.filename, "id": photo.item_id} for photo in photos]

def save_exist_db_with_person(photos, person_id):
    db = SessionLocal()
    blacklisted_ids = set(pid for (pid,) in db.query(PhotoBlacklist.photo_id).all())

    db.query(ExistPerson).delete()

    exit_person_entries = []
    for photo in photos:
        if photo["id"] in blacklisted_ids:
            continue
        ep = ExistPerson(person_id=person_id, photo_id=photo["id"])
        exit_person_entries.append(ep)
    db.bulk_save_objects(exit_person_entries)
    db.commit()

    exit_photos = (
        db.query(Photo)
        .join(ExistPerson, ExistPerson.photo_id == Photo.item_id)
        .filter(ExistPerson.person_id == person_id)
        .all()
    )
    return exit_photos

def save_exit_db_with_album(photos, album_id):
    db = SessionLocal()
    db.query(ExistAlbum).delete()
    exit_album_entries = []
    for photo in photos:
        print(photo["id"])
        ep = ExistAlbum(album_id=album_id, photo_id=photo["id"])
        exit_album_entries.append(ep)
    db.bulk_save_objects(exit_album_entries)
    db.commit()

    exit_photos = (
        db.query(Photo)
        .join(ExistAlbum, ExistAlbum.photo_id == Photo.item_id)
        .filter(ExistAlbum.album_id == album_id)
        .all()
    )
    return exit_photos