#-*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, g, abort
from backend.engine import session
from backend.models import Rubric, Product, Vendor
from update_taxonomy import update_taxonomy
from parse_taxonomy import parse_taxonomy

app = Flask(__name__)

@app.before_request
def before_request():
    g.db = session()
    
@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route("/taxonomy/update/", methods=["POST"])
def taxonomy_update():
    file = request.files["file"]
    if file :
        rows = map(lambda x: x.decode("utf-8"), file.readlines())
        print (rows)
        tax = parse_taxonomy(rows)
        update_taxonomy(tax)
        return redirect(url_for("taxonomy"))
    else:
        abort(502)
        
@app.route("/taxonomy/")
def taxonomy():
    get_axis=lambda x: Rubric.get_children(g.db, rubric=x)
    has_children=lambda x: Rubric.has_children(g.db, x)
    kwargs = {
        "get_axis": get_axis,
        "has_children": has_children
    }
    return render_template("taxonomy.html", **kwargs)
    
@app.route("/taxonomy/rubric/<id>/")
def taxonomy_rubric(id):
    rubric = g.db.query(Rubric).get(int(id))
    if rubric is None : abort(404)
    subrubrics = Rubric.get_children(g.db, rubric=rubric)
    rubric_path = Rubric.get_taxonomy_path(rubric)
    kwargs = {
        "rubric": rubric,
        "subrubrics": subrubrics,
        "rubric_path": rubric_path,
    }
    return render_template("rubric.html", **kwargs)

@app.route("/products/")
def products():
    products = g.db.query(Product).all()
    products_count = g.db.query(Product).count()
    kwargs = {
        "products": products,
        "products_count": products_count
    }
    return render_template("products.html", **kwargs)    

if __name__ == "__main__" :
    app.debug = True
    app.run()
