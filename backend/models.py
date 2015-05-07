#-*- coding: utf-8 -*-

from sqlalchemy import Column, DateTime, String, Text, Integer, ForeignKey, func, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship, backref

Base = declarative_base()

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(128))
    passwd = Column(String(128))
    email = Column(String(128))
    full_name = Column(String(128))
    phone = Column(String(128), nullable=True)
    
class Vendor(Base):
    __tablename__ = "vendor"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    name = Column(String(128))
    desc = Column(Text, nullable=True)
    
    logo = Column(String(255), nullable=True)
    
class Rubric(Base):
    __tablename__ = "rubric"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    name = Column(String(128))
    desc = Column(Text, nullable=True)
    
    logo = Column(String(255), nullable=True)
    path = Column(String(255), nullable=True)
    
    parent_id = Column(Integer, ForeignKey('rubric.id'))

    parent = relationship('Rubric', remote_side=[id])
    
    @staticmethod
    def get_taxonomy_path(rubric):
        path = []
        current = rubric
        while current is not None :
            path.insert(0,current)
            current = current.parent
        return path
        
    @staticmethod
    def has_children(session, rubric):
        return session.query(Rubric).filter(Rubric.parent==rubric).first() is not None
        
    @staticmethod
    def get_children(session, rubric=None):
        return session.query(Rubric).filter(Rubric.parent==(rubric if rubric is not None else None))
    
    @staticmethod
    def get_products(session, rubric=None):
        #return session.query(Product).filter(Rubric.rubrics==(rubric if rubric is not None else None))
        return []
        
class Product(Base):

    __tablename__ = "product"
    
    id = Column(Integer, primary_key=True, autoincrement=True)

    name = Column(String(128))
    desc = Column(Text, nullable=True)
    logo = Column(String(255), nullable=True)
    trade_price = Column(Float, nullable=True)
    retail_price = Column(Float, nullable=True)
    available_for_trade = Column(Boolean, nullable=True)
    available_for_retail = Column(Boolean, nullable=True)
    is_recommend_price = Column(Boolean, nullable=True)
    external_link = Column(String(255))
    trade_by_order = Column(Boolean, nullable=True)
    is_new = Column(Boolean, nullable=True)
    is_special_price = Column(Boolean, nullable=True)
    
    @staticmethod
    def random_products(s, start=0, finish=20):
        order_by_list = [func.random(), func.rand(), 'dbms_random.value']
        for o in order_by_list :
            try:
                return s.query(Product).order_by(o)[start:finish]
            except:
                pass
    
