# -*- coding: utf-8 -*-

from golem.xls.xlstoxml import xls_to_xml_by_path
from lxml import etree
from golem.backend.models import Product, Vendor, Rubric
from golem.backend.engine import session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound
import traceback

def get_rubric(s, rubric_path_by_price):
    try:
        res = s.query(Rubric).filter(Rubric.path.like("%" + rubric_path_by_price + "%")).one()
        return res
    except NoResultFound:
        #print ('No result was found', rubric_path_by_price)
        pass
    except MultipleResultsFound:
        #print ('Multiple results were found', rubric_path_by_price)
        pass
        
def proc_products(s, price):
    for prd in price.xpath("//product"):
        vendor = s.query(Vendor).filter(Vendor.name == prd.get("vendor")).first()
        if vendor is None :
            vendor = Vendor(name=prd.get("vendor"))
            s.add(vendor)
        rubric_path_by_price = "/".join([e for e in prd.xpath("./ancestor-or-self::rubric/@name")]) 
        kw = {
            "name": prd.get("name"),
            "desc": prd.get("short_desc"),
            "vendor": vendor,
            "available_for_trade": prd.get("available_for_trade") == "1",
            "trade_price": float(prd.get("trade_price", 0)),
            "available_for_retail": prd.get("available_for_retail") == "1",
            "retail_price": float(prd.get("retail_price", 0)),
            "external_link": prd.get("external_link"),
            "trade_by_order": prd.get("trade_by_order") == "1",
            "is_new": prd.get("is_new") == "1",
            "is_special_price": prd.get("is_special_price") == "1",
            "is_recommend_price": prd.get("is_recommend_price") == "1",
            "rubric_path_by_price": rubric_path_by_price,
            "rubric": get_rubric(s, rubric_path_by_price), 
        }
        product = Product(**kw)
        s.add(product)

def update_products(price, s=None):
    s = session() if s is None else s
    s.query(Product).delete()
    proc_products(s, price)
    s.commit()

if __name__ == "__main__":
    import sys
    price = xls_to_xml_by_path(sys.argv[1])
    update_products(price)
