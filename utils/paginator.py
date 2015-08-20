# -*- coding: utf-8 -*-

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