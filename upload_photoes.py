# -*- coding: utf-8 -*-

from golem.backend.models import Product, Vendor
import os
import uuid
import shutil
import traceback

def upload_photoes(d, photoes_dir, s, autoremove=False):
	for name in os.listdir(d) :
		
		lpath = os.path.join(d, name)
		if os.path.isfile(lpath):
			lname = lpath.lower() 
			if lname.endswith(".jpg") or lname.endswith(".png") :
				try:
					proc_photo(lpath, photoes_dir, s, autoremove)
				except Exception as e:
					traceback.print_exc()
		elif os.path.isdir(lpath):
			upload_photoes(lpath, photoes_dir, s, autoremove)
		else:
			pass
				
def proc_photo(lpath, photoes_dir, s, autoremove=False):
	name = lpath.lower()
	for vendor in s.query(Vendor).all():
		lvname = vendor.name.lower()
		if lvname in name:
			for product in s.query(Product).filter(Product.vendor == vendor):
				lpname = product.name.lower()
				if lpname in name:
					store(lpath, photoes_dir, s, product, autoremove)

def generate_path():
	return str(uuid.uuid4())[:3]
					
def store(lpath, photoes_dir, s, product, autoremove=False):
	dpath = os.path.join(photoes_dir, generate_path())
	fpath = os.path.join(dpath, str(product.id))
	fpath_small = fpath + "_small"
	if not os.path.exists(dpath):
		os.makedirs(dpath)
	shutil.copy(lpath, fpath)
	shutil.copy(lpath, fpath_small)
	product.photo = fpath
	product.photo_small = fpath_small
	s.add(product)
	if autoremove:
		os.remove(lpath)
	print (fpath)
		
if __name__ == "__main__":
	import sys
	from golem.backend.engine import session
	s = session()
	upload_photoes(sys.argv[1], sys.argv[2], s, autoremove=True)
	s.commit()