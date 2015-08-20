# -*- coding: utf-8 -*-

from flask import url_for

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