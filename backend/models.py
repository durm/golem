#-*- coding: utf-8 -*-

from sqlalchemy import Column, DateTime, String, Text, Integer, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship

Base = declarative_base()
    
class CreatedTrait:

    @declared_attr
    def created_by_id(cls):
        return Column(Integer, ForeignKey('user.id'), index=True)
        
    @declared_attr
    def created_by(cls):
        return relationship(lambda: User, remote_side=id, backref='created_users')
    
class UpdatedTrait:
    
    @declared_attr
    def updated_by_id(cls):
        return Column(Integer, ForeignKey('user.id'), index=True)
        
    @declared_attr
    def updated_by(cls):
        return relationship(lambda: User, remote_side=id, backref='updated_users')
    
class User(Base, CreatedTrait, UpdatedTrait):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    passwd = Column(String)
    email = Column(String)
    full_name = Column(String)
    phone = Column(String)
    
class Proto(Base, CreatedTrait, UpdatedTrait):
    __tablename__ = "proto"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    desc = Column(String)
    
    __mapper_args__ = {
        'polymorphic_identity':'proto',
    }
    
class Rubric(Proto):
    
    __tablename__ = "rubric"
    id = Column(Integer, ForeignKey('proto.id'), primary_key=True)
    logo = Column(String)
    
    __mapper_args__ = {
        'polymorphic_identity':'rubric'
    }
