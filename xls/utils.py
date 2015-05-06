# -*- coding: utf-8 -*-

from golem.xls.macro import *
import hashlib


def md5(s):
    m = hashlib.md5()
    m.update(s)
    return m.hexdigest()


def is_empty(x):
    return x == EMPTY_STRING


def is_by_order(v):
    return v == BY_ORDER


def is_double_dash(v):
    return v == DOUBLE_DASH 


def get_float(v):
    return float(v)


def get_row_values(ws, row):
    return ws.row_values(row, start_colx=0, end_colx=6)


def get_prop(r, i):
    return r[i]


def is_empty_row(r):
    return is_empty(get_prop(r, 0))


def is_rubric(r):
    return not(is_empty(get_prop(r, 0))) and is_empty(get_prop(r, 1)) and is_empty(get_prop(r, 2)) and is_empty(get_prop(r, 5))


def is_product(r):
    return not(is_empty(get_prop(r, 0))) and not(is_empty(get_prop(r, 1))) and not(is_empty(get_prop(r, 2))) and not(is_empty(get_prop(r, 5)))


def get_name(r):
    return get_prop(r, 0)


def get_cell_color_index(wb, ws, row, c):
    cell = ws.cell(row, c)
    xs_ind = cell.xf_index
    xf = wb.xf_list[xs_ind]
    return xf.background.pattern_colour_index


def get_trade_price(r):
    return get_prop(r, 1)


def get_retail_price(r):
    return get_prop(r, 2)


def get_external_link(ws, row):
    link = ws.hyperlink_map.get((row, 5))
    if link is not None :
        return link.url_or_path


def is_product_special_price(wb, ws, row):
    return get_cell_color_index(wb, ws, row, 0) == SPECIAL_PRICE


def is_product_new(wb, ws, row):
    return get_cell_color_index(wb, ws, row, 0) == IS_NEW


def is_recommend_price(wb, ws, row):
    return get_cell_color_index(wb, ws, row, 2) == RECOMMEND_PRICE


def normalize_space(s):
    return " ".join(s.split())

