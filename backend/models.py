#-*- coding: utf-8 -*-

from sqlalchemy import Column, DateTime, String, Text, Integer, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship, backref

Base = declarative_base()
    
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    passwd = Column(String)
    email = Column(String)
    full_name = Column(String)
    phone = Column(String, nullable=True)
    
class Rubric(Base):
    __tablename__ = "rubric"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    name = Column(String)
    desc = Column(String, nullable=True)
    
    logo = Column(String, nullable=True)
    path = Column(String, nullable=True)
    
    parent_id = Column(Integer, ForeignKey('rubric.id'))

    parent = relationship('Rubric', remote_side=[id])
    
    @staticmethod
    def has_children(session, rubric):
        print ("!!!!!", id)
        return session.query(Rubric).filter(Rubric.parent==rubric).first() is not None
        
    @staticmethod
    def get_children(session, rubric=None):
        return session.query(Rubric).filter(Rubric.parent==(rubric if rubric is not None else None))
