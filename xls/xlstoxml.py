# -*- coding: utf-8 -*-

from lxml import etree
import xlrd
from datetime import datetime
from golem.xls.utils import *

def clean_quote(s):
    return s.replace("&quot;","")

def parse_name(fullname):
    parts = fullname.split("|")
    vendor = clean_quote(normalize_space(parts[0]))
    name = clean_quote(normalize_space(parts[1])) if len(parts) >= 2 else None
    short_desc = clean_quote(normalize_space(parts[2])) if len(parts) >= 3 else None
    return (vendor, name, short_desc)

def create_product(wb, ws, row):
    document = etree.Element("product")
    rowValues = get_row_values(ws, row)
    full_name = get_name(rowValues)
    vendor, name, short_desc = parse_name(full_name)
    if name is not None :
        document.set("name", name.capitalize())
    if vendor is not None :
        document.set("vendor", vendor.capitalize())
    if short_desc is not None and short_desc :
        document.set("short_desc", short_desc.capitalize())
    trade_price = get_trade_price(rowValues)
    if not is_double_dash(trade_price) :
        document.set("available_for_trade", "1")
        if is_by_order(trade_price) :
            document.set("trade_by_order", "1")
        else:
            document.set("trade_price", str(trade_price))
    retail_price = get_retail_price(rowValues)
    if not is_double_dash(retail_price) :
        document.set("available_for_retail", "1")
        document.set("retail_price", str(retail_price))
    link = get_external_link(ws, row)
    if link is not None :
        document.set("external_link", link)
    if is_product_new(wb,ws,row) :
        document.set("is_new", "1")
    if is_product_special_price(wb, ws, row):
        document.set("is_special_price", "1")
    if is_recommend_price(wb, ws, row):
        document.set("is_recommend_price", "1")
    return document

def create_rubric(wb, ws, row):
    rubric = etree.Element("rubric")
    rowValues = get_row_values(ws, row)
    rubric.set("name", normalize_space(get_name(rowValues)).capitalize())
    rubric.set("colour_index", str(get_cell_color_index(wb, ws, row, 0)))
    return rubric

def xls_to_xml(wb):
    root_rubric = etree.Element("price")
    ws = wb.sheet_by_index(0)
    current_rubric = root_rubric
    
    for row in range(ws.nrows)[4:]:
        rowValues = get_row_values(ws, row)

        if is_empty_row(rowValues) :
            break

        if is_rubric(rowValues) :
            rubric = create_rubric(wb, ws, row)            

            ci = rubric.get("colour_index")
            same_ci_rubric = current_rubric.xpath("./ancestor-or-self::*[@colour_index = %s]" % str(ci))
            if same_ci_rubric :
                same_ci_rubric = same_ci_rubric[0]
                same_ci_rubric.getparent().append(rubric)
            else:
                if current_rubric.get("colour_index") == "42" :
                    root_rubric.append(rubric)
                else:
                    current_rubric.append(rubric)

            current_rubric = rubric
            #hashsum = md5("|".join(current_rubric.xpath("./ancestor-or-self::rubric/@name")))
            #current_rubric.set("hashsum", hashsum)

        if is_product(rowValues):
            product = create_product(wb, ws, row)
            current_rubric.append(product)

    return root_rubric

def xls_to_xml_by_path(fpath):
    wb = xlrd.open_workbook(fpath, formatting_info=True)
    return xls_to_xml(wb)

def xls_to_xml_by_fileobject(fo):
    wb = xlrd.open_workbook(file_contents=fo.read(), formatting_info=True)
    return xls_to_xml(wb)

if __name__ == "__main__" :

    import sys

    input_xls = sys.argv[1]
    output_xml = sys.argv[2]
   
    ee = xls_to_xml_by_path(input_xls)
    et = etree.ElementTree(ee)
 
    with open(output_xml, "w") as ixls :
        et.write(ixls, encoding="utf-8", pretty_print=True)
