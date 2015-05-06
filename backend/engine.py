#-*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    import aksconf
    DB_URL = aksconf.DB_URL
except:
    DB_URL = "sqlite:///db.sqlite"

engine = create_engine(DB_URL)
session = sessionmaker()
session.configure(bind=engine)

if __name__ == "__main__" :
    from golem.backend.models import Base
    engine = create_engine(DB_URL, echo=True)
    Base.metadata.create_all(engine)
