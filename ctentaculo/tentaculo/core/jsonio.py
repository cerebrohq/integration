# -*- coding: utf-8 -*-
import os, json

def write(jfile, data):
	if data is None or jfile is None: return False

	outtext = json.dumps(data, indent=4, sort_keys=True)

	with open(jfile, 'w') as fh:
		fh.write(outtext)

	return True

def read(jfile):
	result = dict()

	if jfile is None or not os.path.exists(jfile): return result

	lines = ''
	with open(jfile, 'r') as fh:
		lines = fh.read()

	if len(lines) < 1: return result
	result = json.loads(lines)

	return result

def parse(rawtext):
	result = None
	if rawtext is not None and len(rawtext) > 0:
		result = json.loads(rawtext)

	return result
