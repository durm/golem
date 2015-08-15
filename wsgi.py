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

@application.route("/admin/taxonomy/update/", methods=["POST"])
def admin_taxonomy_update():
    file = request.files["file"]
    if file :
        rows = map(lambda x: x.decode("utf-8"), file.readlines())
        tax = parse_taxonomy(rows)
        update_taxonomy(tax)
        return redirect(url_for("taxonomy"))
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
    kwargs = {}
    return render_template("admin/products/price_upload.html", **kwargs)
    
@application.route("/admin/price/parse/", methods=["POST"])
def admin_price_parse():
    file = request.files["file"]
    if file :
        price = xls_to_xml_by_fileobject(file)
        update_products(price)
        return redirect(url_for('admin_price_upload'))
    else:
        abort(502)

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
    return render_template("products/taxonomy_rubric.html", **kwargs)
    
@application.route("/taxonomy/product/<id>/")
def taxonomy_product(id):
    product = g.db.query(Product).get(int(id))
    if product is None: abort(404)
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
    return render_template("list.html", **cls_list_args(cls, h))

def build_url(*args):
    return "/{0}/".format("/".join(args))
    
def build_view_name(*args):
    return "_".join(args)
    
def query_string(args):
    return "&".join(map(lambda x: "=".join(map(str, x)), args.items()))

def add_vendor_predicate(prd_preds, vendor_, vendor, Product):
    if vendor_ != "" and vendor :
        prd_preds.append(Product.vendor_id == vendor_)
    elif vendor and vendor_ == "" :
        prd_preds.append(Product.vendor_id.in_(map(int, vendor)))
    else:
        pass

def add_retail_price_from_predicate(prd_preds, retail_price_from, Product):
    if retail_price_from :
        prd_preds.append(Product.retail_price >= retail_price_from)

def add_retail_price_to_predicate(prd_preds, retail_price_to, Product):
    if retail_price_to :
        prd_preds.append(Product.retail_price <= retail_price_to)

def add_term_predicate(prd_preds, term, Product):		
    if term :
        term = "%{0}%".format(term)
        prd_preds.append(or_(Product.name.like(term), Product.desc.like(term)))

def get_start(start):
    return start if start >= 0 else 0

def get_size(size):
    return size if size > 0 and size <= 20 else 20

class PaginatorUrlBuilder(object):
    
    def __init__(self, view, args, start, size):
        self.view = view
        self.args = args
        self.start = start
        self.size = size
    
    def url_prev(self):
        self.args["start"] = self.start - self.size
        return url_for(self.view, **self.args)
        
    def url_next(self):
        self.args["start"] = self.start + self.size
        return url_for(self.view, **self.args)
    
class Paginator(object):

    def __init__(self, count, start, size):
        self.count = count
        self.start = start
        self.size = size
        
    def has_prev(self):
        return self.start - self.size >= 0
        
    def has_next(self):
        return self.start + self.size < self.count
    
    def need_pagination(self):
        return self.has_prev() or self.has_next()
    
@application.route("/products/search/")
def products_search():

    req = request.args.copy()

    start = get_start(int(request.args.get("start", 0)))
    size = get_size(int(request.args.get("size", 20)))
	
    term = request.args.get("term")
    vendor = request.args.getlist("vendor")
    vendor_ = request.args.get("vendor_", "")
    
    retail_price_from = request.args.get("retail_price_from", 0)    
    retail_price_to = request.args.get("retail_price_to", 0)

    products = g.db.query(Product)
    vendors = g.db.query(Vendor)
    
    prd_preds = []
    
    add_vendor_predicate(prd_preds, vendor_, vendor, Product)
    add_retail_price_from_predicate(prd_preds, retail_price_from, Product)
    add_retail_price_to_predicate(prd_preds, retail_price_to, Product)
    add_term_predicate(prd_preds, term, Product)
    
    vendors_filtered = g.db.query(Vendor).filter(Vendor.id.in_(g.db.query(Product.vendor_id).filter(*prd_preds)))
    
    products = products.filter(*prd_preds)
    products_count = products.count()
    products = products.offset(start).limit(size)
    
    args = request.args.copy()
    psf_args = request.args.copy()
    psf_args.pop("vendor", None)
    
    roots = Rubric.get_children(g.db, rubric=None)
	
    paginator = Paginator(products_count, start, size)
    paginator_url_builder = PaginatorUrlBuilder("products_search", args, start, size)
    
    
    kw = {
        "paginator": paginator,
        "paginator_url_builder": paginator_url_builder, 
        "products": products,
        "products_count": products_count,
        "roots": roots,
        "obj_count": products_count,
        "args": args,
        "vendors": vendors,
        "vendors_filtered": vendors_filtered,
        "psf_args": psf_args,
    }
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
