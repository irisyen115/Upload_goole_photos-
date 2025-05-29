from sqlalchemy import Column, Integer
from sqlalchemy.orm import composite
from models.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableComposite
from sqlalchemy import UniqueConstraint

class PersonPhotoPair:
    def __init__(self, person_id, photo_id):
        self.person_id = person_id
        self.photo_id = photo_id

    def __composite_values__(self):
        return self.person_id, self.photo_id

    def __eq__(self, other):
        return isinstance(other, PersonPhotoPair) and \
               self.person_id == other.person_id and \
               self.photo_id == other.photo_id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return f"PersonPhotoPair(person_id={self.person_id}, photo_id={self.photo_id})"

class ExistPerson(Base):
    __tablename__ = 'exist_person_photos'

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer)
    photo_id = Column(Integer)
    person_photo_pair = composite(PersonPhotoPair, person_id, photo_id)

    photos = relationship("Photo", back_populates="exit_person")

    __table_args__ = (
        UniqueConstraint('person_id', 'photo_id', name='uq_person_photo_pair_exit'),
    )
