import os

from sqlmodel import SQLModel, create_engine
from .models import *


DATABASE_URL = os.environ.get('DB_URL')
engine = create_engine(DATABASE_URL)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
