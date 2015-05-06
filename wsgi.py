#-*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, g, abort, Response
from golem.backend.engine import session
from golem.backend.models import Rubric, Product, Vendor
from golem.update_taxonomy import update_taxonomy
from golem.update_products import update_products
from golem.parse_taxonomy import parse_taxonomy
import traceback
from golem.xls.xlstoxml import xls_to_xml_by_fileobject
from lxml import etree

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
    kwargs = {
        "rubric": rubric,
        "roots": roots,
        "subrubrics": subrubrics,
        "rubric_path": rubric_path,
        "get_axis": get_axis,
        "has_children": has_children,
    }
    return render_template("rubric.html", **kwargs)

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
