#-*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///db.sqlite', echo=True)
session = sessionmaker()
session.configure(bind=engine)

if __name__ == "__main__" :
    from golem.backend.models import Base
    Base.metadata.create_all(engine)
