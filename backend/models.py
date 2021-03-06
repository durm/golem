#-*- coding: utf-8 -*-

from sqlalchemy import Column, DateTime, String, Text, Integer, ForeignKey, func, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship, backref
from golem.utils import get_external_desc

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
        
    def __repr__(self):
        return "{0} ({1})".format(self.name, self.path)
        
class Product(Base):

    __tablename__ = "product"
    
    id = Column(Integer, primary_key=True, autoincrement=True)

    name = Column(String(128))
    desc = Column(Text, nullable=True)
    full_desc = Column(Text, nullable=True)

    vendor_id = Column(Integer, ForeignKey('vendor.id'))
    vendor = relationship('Vendor', backref="product")
    
    rubric_id = Column(Integer, ForeignKey('rubric.id'))
    rubric = relationship('Rubric', backref="product")
    
    rubric_path_by_price = Column(String(256))
    
    photo = Column(String(255), nullable=True)
    photo_small = Column(String(255), nullable=True) 
    trade_price = Column(Float, nullable=True)
    retail_price = Column(Float, nullable=True)
    available_for_trade = Column(Boolean, nullable=True)
    available_for_retail = Column(Boolean, nullable=True)
    is_recommend_price = Column(Boolean, nullable=True)
    external_link = Column(String(255))
    trade_by_order = Column(Boolean, nullable=True)
    is_new = Column(Boolean, nullable=True)
    is_special_price = Column(Boolean, nullable=True)
    
    def get_view_name(self):
        if self.vendor is not None :
            return "{0} {1}".format(self.vendor.name, self.name)
        return self.name if self.name is not None else ""
        
    def get_view_retail_price(self):
        return "{0} руб.".format(self.retail_price)
        
    def get_small_photo_url(self):
        if self.photo_small :
            return "/media/photoes/" + self.photo_small

    def get_photo_url(self):
        if self.photo:
            return "/media/photoes/" + self.photo

    def get_external_desc(self):
        self.full_desc = get_external_desc(self.external_link)

    def __repr__(self):
        return "{0} ({1})".format(self.name, self.rubric_path_by_price)
    
    @staticmethod
    def products(s, start=0, size=20, order_by=None):
        prds = s.query(Product)
        if order_by is not None :
            prds = prds.order_by(order_by)
        return prds.offset(start).limit(size)
    
    @staticmethod
    def random_products(s, start=0, finish=20):
        order_by_list = [func.random(), func.rand(), 'dbms_random.value']
        for o in order_by_list :
            try:
                return s.query(Product).order_by(o).offset(0).limit(finish)
            except:
                pass
        return []
