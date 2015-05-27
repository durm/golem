#-*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, g, abort, Response
from sqlalchemy import func, or_, distinct
from golem.backend.engine import session
from golem.backend.models import Rubric, Product, Vendor
from golem.update_taxonomy import update_taxonomy
from golem.update_products import update_products
from golem.parse_taxonomy import parse_taxonomy
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

@application.route("/taxonomy/update/", methods=["POST"])
def taxonomy_update():
    try:
        file = request.files["file"]
        if file :
            rows = map(lambda x: x.decode("utf-8"), file.readlines())
            tax = parse_taxonomy(rows)
            update_taxonomy(tax)
            return redirect(url_for("taxonomy"))
        else:
            abort(502)
    except Exception as e :
        trace = traceback.format_exc()
        return str(trace)
        
@application.route("/taxonomy/")
def taxonomy():
    get_axis=lambda x: Rubric.get_children(g.db, rubric=x)
    has_children=lambda x: Rubric.has_children(g.db, x)
    kwargs = {
        "get_axis": get_axis,
        "has_children": has_children
    }
    return render_template("taxonomy.html", **kwargs)
    
@application.route("/price/upload/")
def price_upload():
    kwargs = {}
    return render_template("price_upload.html", **kwargs)
    
@application.route("/price/parse/", methods=["POST"])
def price_parse():
    try:
        file = request.files["file"]
        if file :
            price = xls_to_xml_by_fileobject(file)
            update_products(price)
            return redirect(url_for('price_upload'))
        else:
            abort(502)
    except Exception as e :
        trace = traceback.format_exc()
        return str(trace)

@application.route("/", defaults={'id': 0})
@application.route("/taxonomy/rubric/", defaults={'id': 0}) 
@application.route("/taxonomy/rubric/<id>/")
def taxonomy_rubric(id):
    rubric = g.db.query(Rubric).get(int(id))
    roots = Rubric.get_children(g.db, rubric=None)
    if rubric is None and id != 0 : abort(404)
    subrubrics = Rubric.get_children(g.db, rubric=rubric)
    rubric_path = Rubric.get_taxonomy_path(rubric)
    get_axis=lambda x: Rubric.get_children(g.db, rubric=x)
    has_children=lambda x: Rubric.has_children(g.db, x)
    products = Product.random_products(g.db)
    kwargs = {
        "rubric": rubric,
        "roots": roots,
        "subrubrics": subrubrics,
        "rubric_path": rubric_path,
        "get_axis": get_axis,
        "has_children": has_children,
        "products": products,
    }
    return render_template("taxonomy_rubric.html", **kwargs)
    
@application.route("/taxonomy/product/<id>/")
def taxonomy_product(id):
    product = g.db.query(Product).get(int(id))
    if product is None: abort(404)
    kwargs = {
        "product": product,
    }
    return render_template("taxonomy_product.html", **kwargs)

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
    return render_template("list.html", **cls_list_args(cls, h))

def build_url(*args):
    return "/{0}/".format("/".join(args))
    
def build_view_name(*args):
    return "_".join(args)
    
def query_string(args):
    return "&".join(map(lambda x: "=".join(map(str, x)), args.items()))
    
@application.route("/products/search/")
def products_search():
    start = int(request.args.get("start", 0))
    size = int(request.args.get("size", 20))
    if 0 > size > 20 : size = 20
    if 0 > start : start = 0
    roots = Rubric.get_children(g.db, rubric=None)
    
    term = request.args.get("term")
    vendor = request.args.getlist("vendor")
    vendor_ = request.args.get("vendor_", "")
    
    products = g.db.query(Product)
    vendors = g.db.query(Vendor)
    retail_price_from = request.args.get("retail_price_from", 0)
    
    retail_price_to = request.args.get("retail_price_to", 0)
    
    prd_preds = []
    
    if vendor_ != "" and vendor :
        prd_preds.append(Product.vendor_id == vendor_)
    elif vendor and vendor_ == "" :
        prd_preds.append(Product.vendor_id.in_(map(int, vendor)))
    else:
        pass
    if retail_price_from :
        prd_preds.append(Product.retail_price >= retail_price_from)
    if retail_price_to :
        prd_preds.append(Product.retail_price <= retail_price_to)
    
    if term :
        term = "%{0}%".format(term)
        prd_preds.append(or_(Product.name.like(term), Product.desc.like(term)))
        
    vendors_filtered = g.db.query(Vendor).filter(Vendor.id.in_(g.db.query(Product.vendor_id).filter(*prd_preds)))
    
    products = products.filter(*prd_preds)
    products_count = products.count()
    products = products.offset(start).limit(size)
    args = request.args.copy()
    psf_args = request.args.copy()
    psf_args.pop("vendor", None)
    prev_query_args = None
    next_query_args = None
    if start - size >= 0 :
        args["start"] = start - size
        prev_query_args = query_string(args)
    if start + size < products_count :
        args["start"] = start + size
        next_query_args = query_string(args)
    kw = {
        "products": products,
        "products_count": products_count,
        "roots": roots,
        "start": start,
        "size": size,
        "obj_count": products_count,
        "prev": prev_query_args,
        "next": next_query_args,
        "args": args,
        "vendors": vendors,
        "vendors_filtered": vendors_filtered,
        "psf_args": psf_args,
    }
    return render_template("products_search.html", **kw)    
    
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
    
if __name__ == "__main__" :
    application.run()
