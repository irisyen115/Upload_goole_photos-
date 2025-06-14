from sqlalchemy import Column, Integer, Text, DateTime, func
from models.database import Base
from datetime import datetime

class UploadBatch(Base):
    __tablename__ = 'uploaded_batches'

    id = Column(Integer, primary_key=True, autoincrement=True)
    uploaded_by = Column(Text)
    upload_person = Column(Text, default='所有人')
    batch_number = Column(Integer, default=1)
    count = Column(Integer, default=0)
    upload_time = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=datetime.utcnow)