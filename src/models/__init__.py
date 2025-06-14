from .database import Base, engine
from .photo import Photo
from .album import Album
from .person import Person
from .exist_album import ExistAlbum
from .exist_person import ExistPerson
from .photo_blacklist import PhotoBlacklist
from .uploaded_batches import UploadBatch

Base.metadata.create_all(bind=engine)
