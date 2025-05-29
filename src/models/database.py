from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

DATABASE_URL = 'postgresql+psycopg2://user:password@pgsql_photos:5432/photodatabase'

logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
