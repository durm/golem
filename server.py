#-*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for
from backend.engine import session
from backend.models import Rubric
from update_taxonomy import update_taxonomy
from parse_taxonomy import parse_taxonomy

app = Flask(__name__)

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
    s = session()
    get_axis=lambda x: Rubric.get_children(s, rubric=x)
    has_children=lambda x: Rubric.has_children(s, x)
    kwargs = {
        "get_axis": get_axis,
        "has_children": has_children
    }
    return render_template("taxonomy.html", **kwargs)

if __name__ == "__main__" :
    app.debug = True
    app.run()
