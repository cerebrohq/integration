# -*- coding: utf-8 -*-
import sys, subprocess, locale, os, platform, tempfile

# Host os
HOST_OS = platform.system().lower()
# Python version
PY3 = sys.version_info[0] == 3
# Check if python 3.7 (blender new releases)
PY37 = sys.version_info[:2] > (3, 5)

def plugin_dir():
	pdir = os.environ.get("CTENTACULO_LOCATION")
	if pdir is None:
		cdir = os.path.dirname(os.path.realpath(__file__))
		pdir = os.path.normpath(os.path.join(cdir, os.pardir, os.pardir))
	return pdir

def include_libs3():
	# Libs3 paths
	libs3 = [ os.path.join(plugin_dir(), "libs3", HOST_OS, ("python37" if PY37 else "python3") if PY3 else "python2"), os.path.join(plugin_dir(), "libs3", "crossplatform") ]

	for lib in libs3:
		if os.path.exists(lib) and not lib in sys.path:
			sys.path.append(lib)

include_libs3()

def show_dir(fullpath):
	if fullpath is None: return False
	
	path = os.path.normpath(fullpath)

	if not os.path.exists(path):
		return False

	if HOST_OS == "windows":
		if not os.path.isfile(path):
			cmd = u'explorer "{0}"'.format(path)
			if not PY3: cmd = cmd.encode(locale.getpreferredencoding())
			subprocess.Popen(cmd)
		else:
			cmd = u'explorer /select,"{0}"'.format(path)
			if not PY3: cmd = cmd.encode(locale.getpreferredencoding())
			subprocess.Popen(cmd)
	elif HOST_OS == "darwin":
		subprocess.call(['open', '-R', path])
	elif HOST_OS == "linux":
		subprocess.Popen(['xdg-open', path])

	return True

def error_unicode(exception):
	if PY3:
		return str(exception)
	else:
		return string_unicode(exception.message)

def string_unicode(string):
	if PY3:
		if not isinstance(string, str):
			string = str(string.decode('utf-8'))
	else:
		if not isinstance(string, unicode):
			try:
				string = unicode(string.decode('utf-8'))
			except:
				try:
					string = unicode(string.decode(locale.getpreferredencoding()))
				except:
					string = unicode(string)
	return string

def string_byte(string):
	if PY3:
		if isinstance(string, str):
			string = string.encode('utf-8')
	else:
		if isinstance(string, unicode):
			string = string.encode('utf-8')
	return string

def np(path):
	if path is None or not len(path): return path
	return os.path.normpath(os.path.normcase(path))

def getResDir(fname = None):
	if fname is None: fname = ""
	cdir = os.path.dirname(os.path.realpath(__file__))
	resdir = os.path.abspath(os.path.join(cdir, os.pardir, "resources", fname))
	return resdir

def makeFolders(paths = None):
	if paths is None: return False
	badflag = False
	sort_dict = sorted(paths.values())
	for path in sort_dict:
		# TODO: only work with paths? Badflag is no good.
		if os.sep in path or os.altsep in path:
			try:
				os.makedirs(path)
			except OSError as e:
				badflag = True
	if badflag: return False
	return True

def appdatadir():
	home = None
	if HOST_OS == 'windows':
		home = os.environ.get('APPDATA', None)
	elif HOST_OS == 'linux':
		home =  os.path.expanduser('~')			
	elif HOST_OS == 'darwin':
		home = os.path.expanduser('~')
		
	if home is None or not os.path.exists(home):
		raise IOException('HOME directory does not exist: %s' % home)

	return home

def homedir():	
	home = os.path.expanduser('~')	
	if home is None or not os.path.exists(home):
		raise IOException('HOME directory does not exist: %s' % home)

	return os.path.normpath(home)

def configdir():
	'''
	Returns Cerebro config files directory
	'''
	path = appdatadir()
	cerebro = 'cerebro'	
	if HOST_OS == 'linux':	
		cerebro = '.cerebro'	

	path = os.path.normcase(os.path.join(path, cerebro))
	return path

def tempdir():
    temp = tempfile.gettempdir()
    return os.path.normpath(os.path.join(temp, 'tempCerebro'))

def parseInt(strval, default = 0):
	try:
		return int(strval)
	except:
		return default
