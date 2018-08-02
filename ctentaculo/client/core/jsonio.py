# -*- coding: utf-8 -*-
import sys, os
import json as json

ext = '.json'

def getConfigDir():
	appdata = os.environ.get('APPDATA', None)
	jsondir = os.path.join(appdata, 'cerebro')
	return jsondir


def getFilename(jfile):
	if jfile is None: return None
	jsonfile = os.path.join(getConfigDir(), jfile)
	if not jsonfile.endswith(ext): jsonfile = jsonfile + ext
	return jsonfile



def write(jfile = None, d = None):
	'''

	'''
	if d is None or jfile is None: return False
	jsonfile = getFilename(jfile)
	outtext = json.dumps(d, indent=4, sort_keys=True)
	#with open(jsonfile, 'w') as of: json.dump(d, jsonfile)
	with open(jsonfile, 'w') as of: print >> of, outtext
	of.close()
	return True


def read(jfile = None):
	result = dict()
	if jfile is None: return result
	jsonfile = getFilename(jfile)
	if not os.path.exists(jsonfile): return None

	lines = open(jsonfile).read()
	if len(lines) < 1: return None
	result = json.loads(lines)
	return result


def kill(jfile = None):
	if jfile is None: return None
	jsonfile = getFilename(jfile)
	if not os.path.exists(jsonfile): return True
	os.remove(jsonfile)
	return True


# merges 2 dicts
def merge(jfile = None, d = None):
	if d is None: return False
	result = read(jfile)
	if result is None: return False
	result.update(d)
	write(jfile, result)


# adds key and value to json file
def add(jfile = None, k = None, v = None):
	if k is None or v is None: return False
	result = read(jfile)
	if result is None: return False
	tdict = {k:v}
	result.update(tdict)
	write(jfile, result)


# removes key from the json file
def remove(jfile = None, k = None):
	if k is None: return False
	result = read(jfile)
	if k in result:
		try:
			del result[k]
		except KeyError:
			pass
	write(jfile, result)