# -*- coding: utf-8 -*-

from golem.xls.xlstoxml import xls_to_xml_by_path
from lxml import etree
from golem.backend.models import Product
from golem.backend.engine import session

def proc_products(s, price):
    for prd in price.xpath("//product"):
        kw = {
            "name": prd.get("name"),
            "desc": prd.get("short_desc"),
            "available_for_trade": prd.get("available_for_trade") == "1",
            "trade_price": float(prd.get("trade_price")),
            "available_for_retail": prd.get("available_for_retail") == "1",
            "retail_price": float(prd.get("retail_price")),
            "external_link": prd.get("external_link"),
            "trade_by_order": prd.get("trade_by_order") == "1",
            "is_new": prd.get("is_new") == "1",
            "is_special_price": prd.get("is_special_price") == "1",
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
