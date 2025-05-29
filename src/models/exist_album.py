from sqlalchemy import Column, Integer, String, DateTime, Text
from models.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableComposite
from sqlalchemy.orm import composite
from sqlalchemy import UniqueConstraint

class AlbumPhotoPair(MutableComposite):
    def __init__(self, album_id, photo_id):
        self.album_id = album_id
        self.photo_id = photo_id

    def __composite_values__(self):
        return self.album_id, self.photo_id

    def __repr__(self):
        return f"AlbumPhotoPair(album_id={self.album_id}, photo_id={self.photo_id})"

    def __eq__(self, other):
        return isinstance(other, AlbumPhotoPair) and \
               other.album_id == self.album_id and \
               other.photo_id == self.photo_id

class ExistAlbum(Base):
    __tablename__ = 'exist_album_photos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    album_id = Column(Integer)
    photo_id = Column(Integer)
    album_photo_pair = composite(AlbumPhotoPair, album_id, photo_id)

    photos = relationship("Photo", back_populates="exit_album")

    __table_args__ = (
        UniqueConstraint('album_id', 'photo_id', name='uq_album_photo_pair_exit'),
    )
