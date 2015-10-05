# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, g, abort, Response
from sqlalchemy import func, or_, distinct
from golem.backend.engine import session
from golem.backend.models import Rubric, Product, Vendor
from golem.update_taxonomy import update_taxonomy
from golem.update_products import update_products
from golem.parse_taxonomy import parse_taxonomy
from golem.utils import Paginator, PaginatorUrlBuilder
import traceback
from golem.xls.xlstoxml import xls_to_xml_by_fileobject
from lxml import etree
from functools import reduce

application = Flask(__name__)
application.debug = True

@application.before_request
def before_request():
    g.db = session()
    
@application.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@application.route("/admin/taxonomy/update/", methods=["POST"])
def admin_taxonomy_update():
    file = request.files["file"]
    if file:
        rows = map(lambda x: x.decode("utf-8"), file.readlines())
        tax = parse_taxonomy(rows)
        update_taxonomy(tax)
        return redirect(url_for("admin_taxonomy"))
    else:
        abort(502)
        
@application.route("/admin/taxonomy/")
def admin_taxonomy():
    get_axis=lambda x: Rubric.get_children(g.db, rubric=x)
    has_children=lambda x: Rubric.has_children(g.db, x)
    kwargs = {
        "get_axis": get_axis,
        "has_children": has_children
    }
    return render_template("admin/products/taxonomy.html", **kwargs)
    
@application.route("/admin/price/upload/")
def admin_price_upload():
    return render_template("admin/products/price_upload.html")
    
@application.route("/admin/price/parse/", methods=["POST"])
def admin_price_parse():
    file = request.files["file"]
    if file:
        price = xls_to_xml_by_fileobject(file)
        update_products(price)
        return redirect(url_for('admin_price_upload'))
    else:
        abort(502)

@application.route("/", defaults={'id': 0})
@application.route("/taxonomy/rubric/", defaults={'id': 0})
@application.route("/taxonomy/rubric/<id>/")
def taxonomy_rubric(id):

    req = request.args.copy()
    rubric = g.db.query(Rubric).get(id)

    if id == 0 :
        results = {
            "products": Product.random_products(g.db), 
            "products_count": 20,
        }
        pagination = None
    else:
    
        start = get_start(int(req.get("start", 0)))
        size = get_size(int(req.get("size", 20)))
        
        predicates = [get_rubric_predicate(rubric)]
        
        results = product_search_results(predicates, start, size)
        pagination = product_search_results_paginator(results, "taxonomy_rubric", req, start, size)

    roots = Rubric.get_children(g.db, rubric=None)
    
    subrubrics = Rubric.get_children(g.db, rubric=rubric)
    rubric_path = Rubric.get_taxonomy_path(rubric)
    get_axis=lambda x: Rubric.get_children(g.db, rubric=x)
    has_children=lambda x: Rubric.has_children(g.db, x)
    
    kw = {
        "rubric": rubric,
        "roots": roots,
        "subrubrics": subrubrics,
        "rubric_path": rubric_path,
        "get_axis": get_axis,
        "has_children": has_children,
    }
    
    kw.update(results)
    if pagination is not None :
        kw.update(pagination)
    
    return render_template("products/taxonomy_rubric.html", **kw)
    
@application.route("/taxonomy/product/<id>/")
def taxonomy_product(id):
    product = g.db.query(Product).get(int(id))
    if product is None:
        abort(404)
    kwargs = {
        "product": product,
    }
    return render_template("products/taxonomy_product.html", **kwargs)

def cls_list_args(cls, h):
    objs = g.db.query(cls).all()
    objs_count = g.db.query(cls).count()
    return {
        "objs": objs,
        "objs_count": objs_count,
        "h": h,
        "create_url": build_view_name(cls.__tablename__, "create"),
        "edit_url": build_view_name(cls.__tablename__, "edit"),
        "delete_url": build_view_name(cls.__tablename__, "delete"),
    }
    
def cls_list(cls, h):
    return render_template("admin/list.html", **cls_list_args(cls, h))

def build_url(*args):
    return "/{0}/".format("/".join(args))
    
def build_view_name(*args):
    return "_".join(args)
    
def query_string(args):
    return "&".join(map(lambda x: "=".join(map(str, x)), args.items()))

def get_vendor_predicate(req):
    vendor = req.getlist("vendor")
    vendor_ = req.get("vendor_", "")
    if vendor_ != "" and vendor :
        return Product.vendor_id == vendor_
    elif vendor and vendor_ == "" :
        return Product.vendor_id.in_(map(int, vendor))
    else:
        pass

def get_retail_price_from_predicate(req):
    retail_price_from = req.get("retail_price_from", 0)
    if retail_price_from :
        return Product.retail_price >= retail_price_from

def get_retail_price_to_predicate(req):
    retail_price_to = req.get("retail_price_to", 0)
    if retail_price_to :
        return Product.retail_price <= retail_price_to

def get_term_predicate(req):		
    term = req.get("term")
    if term :
        term = "%{0}%".format(term)
        return or_(Product.name.like(term), Product.desc.like(term))
        
def get_rubric_predicate(rubric):
    if rubric :
        return Product.rubric == rubric
        
def get_predicates(req):
    p =  list(
        filter(
            lambda x: x is not None, 
            [
                get_vendor_predicate(req),
                get_retail_price_from_predicate(req),
                get_retail_price_to_predicate(req),
                get_term_predicate(req),
            ]
        )
    )
    return p
    
def get_start(start):
    return start if start >= 0 else 0

def get_size(size):
    return size if size > 0 and size <= 20 else 20

def get_vendors_filtered(predicates):
    return g.db.query(Vendor).filter(Vendor.id.in_(g.db.query(Product.vendor_id).filter(*predicates)))

def get_products_filtered(predicates):
    return g.db.query(Product).filter(*predicates)
    
def product_search_results(predicates, start, size):
    
    products = get_products_filtered(predicates)
    
    products_count = products.count()
    products = products.offset(start).limit(size)
    
    return {
        "products_count":products_count,
        "products": products,
    }
    
def product_search_results_paginator(results, view, req, start, size):
    
    paginator = Paginator(results["products_count"], start, size)
    paginator_url_builder = PaginatorUrlBuilder(view, req, start, size, url_for)
    
    return {
        "paginator": paginator,
        "paginator_url_builder": paginator_url_builder,
    }
    
@application.route("/products/search/")
def products_search():

    req = request.args.copy()

    start = get_start(int(req.get("start", 0)))
    size = get_size(int(req.get("size", 20)))
    
    predicates = get_predicates(req)
    
    results = product_search_results(predicates, start, size)
    pagination = product_search_results_paginator(results, "products_search", req, start, size)
    
    vendors = g.db.query(Vendor)
    vendors_filtered = get_vendors_filtered(predicates)
    
    roots = Rubric.get_children(g.db, rubric=None)
	
    kw = {
        "roots": roots,
        "args": req,
        "vendors": vendors,
        "vendors_filtered": vendors_filtered,
    }
    
    kw.update(results)
    kw.update(pagination)
    
    return render_template("products/products_search.html", **kw)    
    
@application.route(build_url(Rubric.__tablename__))
def rubric(): return cls_list(Rubric, "Рубрики")

@application.route(build_url(Product.__tablename__))
def product(): return cls_list(Product, "Продукты")   

@application.route(build_url(Vendor.__tablename__))
def vendor(): return cls_list(Vendor, "Производители")

def cls_list_delete(s, cls, ids):
    s.query(cls).filter(cls.id.in_(ids)).delete(synchronize_session=False)
    s.commit()

def cls_list_delete_view(s, cls, ids):
    cls_list_delete(s, cls, ids)
    return redirect(url_for(build_view_name(cls.__tablename__)))

@application.route(build_url(Rubric.__tablename__, "delete"), methods=["post"])
def rubric_delete(): return cls_list_delete_view(g.db, Rubric, request.form.getlist("obj"))

@application.route(build_url(Vendor.__tablename__, "delete"), methods=["post"])
def vendor_delete(): return cls_list_delete_view(g.db, Vendor, request.form.getlist("obj"))

@application.route(build_url(Product.__tablename__, "delete"), methods=["post"])
def product_delete(): return cls_list_delete_view(g.db, Product, request.form.getlist("obj"))

@application.route(build_url(Rubric.__tablename__, "create"))
def rubric_create(): return "rubric create"

@application.route(build_url(Vendor.__tablename__, "create"))
def vendor_create(): return "vendor create"

@application.route(build_url(Product.__tablename__, "create"))
def product_create(): return "product create"

@application.route(build_url(Rubric.__tablename__, "edit", "<id>"))
def rubric_edit(id): return "rubric edit " + str(id)

@application.route(build_url(Vendor.__tablename__, "edit", "<id>"))
def vendor_edit(id): return "vendor edit " + str(id)

@application.route(build_url(Product.__tablename__, "edit", "<id>"))
def product_edit(id): return "product edit " + str(id)

@application.route("/admin/function_list/")
def function_list():
    return render_template("admin/function_list.html")

if __name__ == "__main__" :
    application.run()
