# -*- coding: utf-8 -*-

from lxml import etree
import xlwt
from datetime import datetime


def xls_write_top(ws, price_desc=" "):
    style_string = "borders: top medium, bottom medium, left medium, right medium"
    style = xlwt.easyxf(style_string)
    ws.write(0, 0, u"Прайс%sсгенерирован %s" % (price_desc, str(datetime.now())))
    ws.write(1, 0, u"Наименование товара", style)
    ws.write(1, 1, u"Цена", style)
    ws.write(1, 2, u"Ссылка", style)


def write_product(ws, r, product, product_style):
    r += 1
    ws.write(r, 0, "%s | %s | %s" % (product.get("vendor", ""), product.get("name", ""), product.get("short_desc", "")), product_style)
    ws.write(r, 1, product.get("price", ""), product_style)
    ws.write(r, 2, product.get("url", ""), product_style)
    return r


def get_rubric_style(ci):
    style = xlwt.XFStyle()
    pattern = xlwt.Pattern()
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    pattern.pattern_fore_colour = ci
    style.pattern = pattern
    style.font.colour_index = xlwt.Style.colour_map['white']
    style.font.bold = True
    return style


def write_rubric(ws, r, rubric, style, product_style):
    r += 1
    ws.write(r, 0, rubric.get("name"), style)
    ws.write(r, 1, "", style)
    ws.write(r, 2, "", style)
    for item in rubric :
        if item.tag == "rubric":
            r = write_rubric(ws, r, item, get_rubric_style(int(item.get("colour_index"))), product_style)
        if item.tag == "product":
            r = write_product(ws, r, item, product_style)
    return r


def xml_to_xls(root_rubric):   
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Page1')
    xls_write_top(ws)
    style_string = "borders: top medium, bottom medium, left medium, right medium"
    style = xlwt.easyxf(style_string)
    product_style_string = "borders: bottom thin, left thin, right thin"
    product_style = xlwt.easyxf(style_string)
    col = ws.col(0)
    col.width = 1200 * 20
    r = 1
    for rubric in root_rubric :
        r = write_rubric(ws, r, rubric, style, product_style)
    return wb


def xml_to_xls_by_path(fpath):
    root_rubric = etree.parse(fpath).getroot()
    return xml_to_xls(root_rubric)


if __name__ == "__main__" :
    import sys
    input_xml = sys.argv[1]
    output_xsl = sys.argv[2]
    xml_to_xls_by_path(input_xml).save(output_xsl) 
