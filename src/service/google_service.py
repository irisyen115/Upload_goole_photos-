from service.synology_service import (
    save_photos_to_db_with_album, save_exit_db_with_person,
    save_photos_to_db_with_person, randam_pick_from_person_database,
    randam_pick_from_album_database, save_exit_db_with_album
)
from lib.synlogy import list_photos_by_album, list_photos_by_person

def get_photos_upload_to_album(auth, person_ID, album_ID, upload_photo_num):
    random_photos = []

    if person_ID:
        person_photo_list = list_photos_by_person(auth=auth, person_id=person_ID, limit=upload_photo_num)
        save_photos_to_db_with_person(person_photo_list, person_ID)
        random_photos = randam_pick_from_person_database(person_id=person_ID, limit=upload_photo_num)
        exit_person_filename = [photo.filename for photo in save_exit_db_with_person(person_id=person_ID, photos=random_photos)]
        print(f"現存於Google相簿照片檔名: {exit_person_filename}")
    elif album_ID:
        album_photo_list = list_photos_by_album(auth=auth, album_id=album_ID, limit=upload_photo_num)
        save_photos_to_db_with_album(album_photo_list, album_ID)
        random_photos = randam_pick_from_album_database(album_id=album_ID, limit=upload_photo_num)
        exit_album_filename = [photo.filename for photo in save_exit_db_with_album(album_id=album_ID, photos=random_photos)]
        print(f"現存於Google相簿照片檔名: {exit_album_filename}")
    return random_photos