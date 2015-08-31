# -*- coding: utf-8 -*-

from golem.backend.models import Product, Vendor, Rubric
from golem.backend.engine import session

s = session()

for prd in s.query(Product).filter(Product.full_desc is None):
    prd.get_external_desc()
    s.add(prd)
    
s.commit()
