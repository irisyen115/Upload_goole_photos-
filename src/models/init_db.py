from models.database import Base, engine
from models.photo import Photo
from models.album import Album
from models.person import Person
from models.exist_album import ExistAlbum
from models.exist_person import ExistPerson

Base.metadata.create_all(bind=engine)
