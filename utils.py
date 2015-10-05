#-*- codng: utf-8 -*-

import uuid
import urllib
from lxml import html, etree
import html2text
import tempfile
import os

try:
    from PIL import Image, ImageOps
except ImportError:
    import Image
    import ImageOps

def html_to_text(html_desc):
    h = html2text.HTML2Text()
    h.ignore_links = True
    return h.handle(html_desc)

def get_external_desc(url):
    try:
        parser = etree.HTMLParser(encoding='cp1251')
        page = html.parse(url, parser).getroot()
        hd = etree.tostring(page.xpath('//div[@class="fulltext"]')[0], encoding="utf-8")
        md = html_to_text(hd.decode("utf-8"))
        return md
    except:
        return None

def get_id():
    return str(uuid.uuid4())

def retrieve(url, fname):
    urllib.urlretrieve(url, fname)

def add_watermark(orig, mark, dest=None, thumbnail=None):
    baseim = Image.open(orig)
    logoim = Image.open(mark)
    baseim.paste(logoim, (baseim.size[0]-logoim.size[0], baseim.size[1]-logoim.size[1]))
    if thumbnail is not None:
        baseim.thumbnail(thumbnail)
    if dest is None :
        dest = orig
    baseim.convert("RGB").save(dest,"JPEG")
    
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
    
class PaginatorUrlBuilder(object):
    
    def __init__(self, view, args, start, size, urf_for):
        self.view = view
        self.args = args
        self.start = start
        self.size = size
        self.url_for = urf_for
    
    def url_prev(self):
        self.args["start"] = self.start - self.size
        return self.url_for(self.view, **self.args)
        
    def url_next(self):
        self.args["start"] = self.start + self.size
        return self.url_for(self.view, **self.args)