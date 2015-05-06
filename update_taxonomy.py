#-*- coding: utf-8 -*-

from golem.parse_taxonomy import parse_taxonomy
from lxml import etree
from golem.backend.models import Rubric
from golem.backend.engine import session

def create_rubrics(s, tax, parent=None):
    for rubric in tax :
        r = Rubric(name=rubric.get("name"), path=rubric.get("path"), parent=parent)
        s.add(r)
        create_rubrics(s, rubric, r)

def update_taxonomy(tax, s=None):
    s = session() if s is None else s
    s.query(Rubric).delete()
    create_rubrics(s, tax)
    s.commit()
    
if __name__ == "__main__" :
    import sys
    from lxml import etree
    with open(sys.argv[1]) as f :
        tax = parse_taxonomy(f)
        update_taxonomy(tax)
