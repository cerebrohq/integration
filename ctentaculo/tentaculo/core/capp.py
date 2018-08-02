# -*- coding: utf-8 -*-
import sys, os, locale, platform, shutil, subprocess, tempfile

# Define messages display
DEBUG = False
try:
	from tentaculo import debug
	DEBUG = debug.DEBUG
except ImportError:
	pass

HOST = 0
# Supported hosts
STANDALONE = 0
MAYA = 10
MAYA2 = 11
NUKE = 20
HOUDINI = 30
BLENDER = 40
C4D = 50
MAX = 60

# Host file extensions
MAYA_EXT = ['.ma', '.mb']
NUKE_EXT = ['.nk']
HOUDINI_EXT = ['.hip']
MAX_EXT = ['.max']
C4D_EXT = ['.c4d']
BLENDER_EXT = ['.blend']
HOST_EXT = MAYA_EXT + NUKE_EXT + HOUDINI_EXT + MAX_EXT + C4D_EXT + BLENDER_EXT
HOST_NAME = 'Standalone'

# Host os
HOST_OS = platform.system().lower()
# Python version
PY3 = sys.version_info[0] == 3

def plugin_dir():
	pdir = os.environ.get("CTENTACULO_LOCATION")
	if pdir is None:
		cdir = os.path.dirname(os.path.realpath(__file__))
		pdir = os.path.normpath(os.path.join(cdir, os.pardir, os.pardir))
	return pdir

def include_libs3():
	# Libs3 paths
	libs3 = [ os.path.join(plugin_dir(), "libs3", HOST_OS, "python3" if PY3 else "python2"), os.path.join(plugin_dir(), "libs3", "crossplatform") ]

	for lib in libs3:
		if os.path.exists(lib) and not lib in sys.path:
			sys.path.append(lib)

include_libs3()

# Define host application
try:
	from shiboken import wrapInstance
	import maya.cmds as mc
	import maya.mel as mel
	import pymel.core as pm
	import maya.OpenMaya as om
	import maya.OpenMayaUI as omui
	HOST = MAYA
	HOST_EXT = MAYA_EXT
	HOST_NAME = 'maya'
	os.environ['QT_PREFERRED_BINDING'] = os.pathsep.join(['PySide2', 'PySide', 'PyQt4'])
except ImportError:
	pass

try:
	from shiboken2 import wrapInstance
	import maya.cmds as mc
	import maya.mel as mel
	import pymel.core as pm
	import maya.OpenMaya as om
	import maya.OpenMayaUI as omui
	HOST = MAYA2
	HOST_EXT = MAYA_EXT
	HOST_NAME = 'maya'
	os.environ['QT_PREFERRED_BINDING'] = os.pathsep.join(['PySide2', 'PySide', 'PyQt4'])
except ImportError:
	pass

try:
	import nuke
	import nukescripts
	HOST = NUKE
	HOST_EXT = NUKE_EXT
	HOST_NAME = 'nuke'
	os.environ['QT_PREFERRED_BINDING'] = os.pathsep.join(['PySide2', 'PySide', 'PyQt4'])
except ImportError:
	pass

try:
	import hou
	HOST = HOUDINI
	HOST_EXT = HOUDINI_EXT
	HOST_NAME = 'houdini'
	os.environ['QT_PREFERRED_BINDING'] = os.pathsep.join(['PySide2', 'PySide', 'PyQt4'])
except ImportError:
	pass

try:
	import bpy
	HOST = BLENDER
	HOST_NAME = 'blender'
	HOST_EXT = BLENDER_EXT
	os.environ['QT_PREFERRED_BINDING'] = 'PyQt5'
except ImportError:
	pass

try:
	import c4d
	HOST = C4D
	HOST_NAME = 'cinema4d'
	HOST_EXT = C4D_EXT
	os.environ['QT_PREFERRED_BINDING'] = 'PyQt4'
except ImportError:
	pass

try:
	import MaxPlus
	HOST = MAX
	HOST_EXT = MAX_EXT
	HOST_NAME = '3dsmax'
	os.environ['QT_PREFERRED_BINDING'] = os.pathsep.join(['PySide2', 'PySide', 'PyQt4'])
except ImportError:
	pass

from tentaculo import Qt

if HOST == C4D or HOST == BLENDER:
	if PY3:
		Qt.QtCore.QCoreApplication.addLibraryPath(os.path.join(plugin_dir(), "libs3", HOST_OS, "python3", "PyQt5", "plugins"))
	app = Qt.QtWidgets.QApplication(sys.argv)

QT5 = Qt.__binding__ in ["PySide2", "PyQt5"]


def string_unicode(string):
	if PY3:
		if not isinstance(string, str):
			string = str(string.decode('utf-8'))
	else:
		if not isinstance(string, unicode):
			try:
				string = unicode(string.decode('utf-8'))
			except:
				string = unicode(string.decode(locale.getpreferredencoding()))
	return string

def string_byte(string):
	if PY3:
		if isinstance(string, str):
			string = string.encode('utf-8')
	else:
		if isinstance(string, unicode):
			string = string.encode('utf-8')
	return string

def debugMsg(msg = None):
	if DEBUG is True:
		print(msg)

def showDir(fullpath = None):
	if fullpath is None: return
	
	path = os.path.normpath(fullpath)

	if not os.path.exists(path):
		debugMsg(u"[!] Path doesn't exist : {0}".format(path))
		return None

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

def copyToClipboard(text = None):
	if text is None: return
	clipboard = Qt.QtWidgets.QApplication.clipboard()
	clipboard.setText(text)

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

def open_file(log, filepath, origin_path = None):
	if not os.path.exists(filepath):
		raise Exception('{0} does not exist'.format(filepath))

	if origin_path is None: origin_path = filepath

	if HOST == STANDALONE:
		log.debug('Open: Standalone {0}'.format(fname))
	elif HOST == MAYA or HOST == MAYA2:
		check_workspace_maya(log, origin_path)
		mc.file(new = True, force = True)
		mc.file(filepath, open = True, force = True)
		log.debug('Maya openned %s', filepath)
	elif HOST == NUKE:
		nuke.scriptClear()
		nuke.Root().setModified(False)
		nuke.scriptOpen(filepath)
		log.debug("Nuke opened %s", filepath)
	elif HOST == HOUDINI:
		hou.hipFile.load(filepath.replace('\\', '/'), suppress_save_prompt = True)
		log.debug("Houdini opened %s", filepath)
	elif HOST == MAX:
		MaxPlus.FileManager.Open(filepath)
		log.debug("Max opened %s", filepath)
	elif HOST == C4D:
		c4d.documents.LoadFile(str(filepath.replace('\\', '/')))
		log.debug("Cinema 4D opened %s", filepath)
	elif HOST == BLENDER:
		bpy.ops.wm.open_mainfile(filepath = filepath)
		log.debug("Blender opened %s", filepath)

	return filepath

def create_file(log, filepath, origin_path = None):
	dir = os.path.dirname(filepath)
	if not os.path.exists(dir):
		raise Exception('{0} does not exist'.format(dir))

	if origin_path is None: origin_path = filepath

	if HOST == STANDALONE:
		log.debug("New file: Standalone")
	elif HOST == MAYA or HOST == MAYA2:
		check_workspace_maya(log, origin_path)
		mc.file(new = True, force = True)
		mc.file(rename = filepath)
		mc.file(save = True, type = "mayaAscii")
	elif HOST == NUKE:
		nuke.scriptClear()
		nuke.scriptSaveAs(filepath, overwrite = 1)
	elif HOST == HOUDINI:
		hou.hipFile.clear(suppress_save_prompt = True)
		hou.hipFile.save(filepath)
	elif HOST == MAX:
		MaxPlus.FileManager.Reset(noPrompt = True)
		MaxPlus.FileManager.Save(filepath)
	elif HOST == C4D:
		c4d.documents.CloseAllDocuments()
		newDoc = c4d.documents.BaseDocument()
		c4d.documents.InsertBaseDocument(newDoc)
		c4d.documents.SaveDocument(newDoc, str(filepath), c4d.SAVEDOCUMENTFLAGS_0, c4d.FORMAT_C4DEXPORT)
		c4d.documents.LoadFile(str(filepath))
	elif HOST == BLENDER:
		bpy.ops.wm.read_homefile()
		bpy.ops.wm.save_mainfile(filepath = filepath, check_existing = False)

	return filepath

def file_name(log):
	file_name = None

	if HOST == STANDALONE:
		log.debug("Request file name: Standalone")
	elif HOST == MAYA or HOST == MAYA2:
		file_name = os.path.normpath(mc.file(query = True, sceneName = True))
	elif HOST == NUKE:
		file_name = os.path.normpath(nuke.root().name())
	elif HOST == HOUDINI:
		file_name = os.path.normpath(hou.hipFile.name())
	elif HOST == MAX:
		file_name = MaxPlus.FileManager.GetFileNameAndPath()
	elif HOST == C4D:
		doc = c4d.documents.GetActiveDocument()
		if doc is not None:
			file_name = os.path.join(doc.GetDocumentPath(), doc.GetDocumentName())
	elif HOST == BLENDER:
		if bpy.data.is_saved:
			file_name = bpy.data.filepath

	return file_name

def save_query(log):
	cancel = False

	if HOST == STANDALONE:
		log.debug("Query user file save: Standalone")
	elif HOST == MAYA or HOST == MAYA2:
		file_name = mc.file(query = True, sceneName = True)
		need_save = mc.file(query = True, modified = True)
		if len(file_name) > 0 and need_save:
			ret = mc.confirmDialog(title='Closing file', message='Save current file?', messageAlign='center', button=['Yes', 'No', 'Cancel'], defaultButton='Yes', cancelButton='Cancel', dismissString='Cancel')
			if ret == "Yes":
				mc.file(save = True, type = "mayaAscii")
			elif ret == "Cancel":
				cancel = True
	elif HOST == NUKE:
		cancel = not nuke.scriptClose()
	elif HOST == HOUDINI:
		need_save = hou.hipFile.hasUnsavedChanges()
		if need_save:
			hou.hipFile.clear()
			cancel = hou.hipFile.hasUnsavedChanges()
	elif HOST == MAX:
		cancel = not MaxPlus.FileManager.CheckForSave()
	elif HOST == C4D:
		doc = c4d.documents.GetActiveDocument()
		if doc is not None and doc.GetChanged():
			cancel = not c4d.documents.SaveDocument(doc, doc.GetDocumentPath() + "/" + doc.GetDocumentName(), c4d.SAVEDOCUMENTFLAGS_DIALOGSALLOWED, c4d.FORMAT_C4DEXPORT)
	elif HOST == BLENDER:
		if bpy.data.is_dirty:
			bpy.ops.wm.save_mainfile(check_existing = True)
			cancel = bpy.data.is_dirty

	return not cancel

def save_file(log, fname = None):
	if fname is None: fname = "temp"
	file_path = fname

	if HOST == STANDALONE:
		log.debug("Save: Standalone {0}".format(file_path))
	elif HOST == MAYA or HOST == MAYA2:
		savef = mc.file(query = True, sceneName = True)
		#if len(savef) == 0:
		mc.file(rename = file_path)
		savef = mc.file(save = True, type = "mayaAscii")
	elif HOST == NUKE:
		savef = file_path
		nuke.scriptSaveAs(file_path, overwrite = 1)
	elif HOST == HOUDINI:
		hou.hipFile.setName(file_path)
		hou.hipFile.save()
		savef = os.path.normpath(file_path)
	elif HOST == MAX:
		savef = file_path
		MaxPlus.FileManager.Save(file_path)
	elif HOST == C4D:
		savef = file_path
		doc = c4d.documents.GetActiveDocument()
		if doc is not None:
			c4d.documents.SaveDocument(doc, str(file_path), c4d.SAVEDOCUMENTFLAGS_0, c4d.FORMAT_C4DEXPORT)
	elif HOST == BLENDER:
		savef = file_path
		bpy.ops.wm.save_mainfile(filepath = file_path)

	return savef

def import_file(log, fname = None, as_reference = False):
	if fname is None or not os.path.exists(fname):
		log.error("Invalid file path given for import: %s", fname)
		return False

	if HOST == STANDALONE:
		log.debug("Import: Standalone %s", fname)
	elif HOST == MAYA or HOST == MAYA2:
		log.debug("Import: Maya %s", fname)
		if as_reference:
			file_path = mc.file(fname, reference = True, mergeNamespacesOnClash = True)
			mc.file(file_path, selectAll = True)
		else:
			before = mc.ls()
			mc.file(fname, i = True, mergeNamespacesOnClash = True)
			after = mc.ls()
			selection = [x for x in after if x not in before]
			mc.select(selection)
	elif HOST == NUKE:
		log.debug("Import: Nuke %s", fname)
		if as_reference:
			nuke.nodes.Read(file = fname)
	elif HOST == HOUDINI:
		log.debug("Import: Houdini %s", fname)
		if as_reference:
			pass
		else:
			hou.hipFile.merge(fname)
	elif HOST == MAX:
		log.debug("Import: 3ds Max %s", fname)
		if as_reference:
			pass
		else:
			MaxPlus.FileManager.Merge(fname, True, True)
	elif HOST == C4D:
		log.debug("Import: C4D %s", fname)
		doc = c4d.documents.GetActiveDocument()
		if doc is not None:
			if as_reference:
				pass
			else:
				c4d.documents.MergeDocument(doc, fname)
	elif HOST == BLENDER:
		log.debug("Import: Blender %s", fname)
		with bpy.data.libraries.load(filepath = fname, link = as_reference) as (data_from, data_to):
			#data_to.objects = data_from.objects
			for attr in dir(data_to):
				setattr(data_to, attr, getattr(data_from, attr))

		for obj in data_to.objects:
			if obj is not None:
				bpy.context.scene.objects.link(obj)
				obj.select = True

	return True

# Global app_window(): choose the main parent window depending on environment
def app_window():
	parent = None
	if HOST == MAYA or HOST == MAYA2:
		mayaMainWindowPtr = omui.MQtUtil.mainWindow()
		mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), Qt.QtWidgets.QWidget)
		parent = mayaMainWindow
	elif HOST == HOUDINI:
		#hou.ui.mainQtWindow()
		parent = hou.qt.mainWindow()
	elif HOST == NUKE:
		for obj in Qt.QtWidgets.QApplication.topLevelWidgets():
			if (obj.inherits('QMainWindow') and	obj.metaObject().className() == 'Foundry::UI::DockMainWindow'):
				parent = obj
	elif HOST == MAX:
		try:
			parent = MaxPlus.GetQMaxMainWindow() if QT5 else MaxPlus.GetQMaxWindow()
		except:
			# Max 2016
			pass
	elif HOST == C4D:
		# TODO: No Qt windows. Mb transform main window handle?
		pass
	elif HOST == BLENDER:
		# TODO: No Qt windows. Mb transform main window handle?
		pass

	return parent

# Focus in/out host for host application

def focus_in():
	if HOST == MAYA or HOST == MAYA2:
		pass
	elif HOST == HOUDINI:
		pass
	elif HOST == NUKE:
		pass
	elif HOST == MAX:
		MaxPlus.CUI.DisableAccelerators()
	elif HOST == C4D:
		pass
	elif HOST == BLENDER:
		pass

def focus_out():
	if HOST == MAYA or HOST == MAYA2:
		pass
	elif HOST == HOUDINI:
		pass
	elif HOST == NUKE:
		pass
	elif HOST == MAX:
		MaxPlus.CUI.EnableAccelerators()
	elif HOST == C4D:
		pass
	elif HOST == BLENDER:
		pass

# Global clearUI(): delete window UI if necessary
def clearUI(window = None):
	if not window is None:
		if HOST == MAYA or HOST == MAYA2:
			if pm.window(window, q=True, exists=True):
				pm.deleteUI(window)

def platform_name():
	return platform.system().lower()

def check_workspace_maya(log, path):
	if path is None: return None

	log.info("Looking for workspace from %s", path)

	if os.path.isfile(path):
		path = os.path.normpath(os.path.dirname(path))
	else:
		path = os.path.normpath(path)

	ws_dir = None
	ws_file = r"workspace.mel"

	dir_list = { os.path.normpath(os.path.join(path, (os.pardir + os.sep) * i)) for i in range(len(path.split(os.sep))) }

	for d in sorted(dir_list, reverse=True):
		if os.path.exists(d) and ws_file in os.listdir(d):
			ws_dir = d
			break

	if ws_dir is not None:
		log.info("Setting Maya workspace to %s", ws_dir)
		ws_dir = mc.workspace(ws_dir, openWorkspace=True)

	return ws_dir

def appdatadir():
		host = platform_name()
		home = None
		if host == 'windows':
			home = os.environ.get('APPDATA', None)
		elif host == 'linux':
			home =  os.path.expanduser('~')			
		elif host == 'darwin':
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
	plat = platform_name()
	cerebro = 'cerebro'	
	if plat == 'linux':	
		cerebro = '.cerebro'	

	path = os.path.normcase(os.path.join(path, cerebro))
	return path

def tempdir():
    temp = tempfile.gettempdir()
    return os.path.normpath(os.path.join(temp, 'tempCerebro'))

if DEBUG is True:
	if HOST == STANDALONE:
		print('host(): Standalone')
	elif HOST == MAYA:
		print('host(): Maya16-')
	elif HOST == MAYA2:
		print('host(): Maya17+')
	elif HOST == NUKE:
		print('host(): Nuke')
	elif HOST == HOUDINI:
		print('host(): Houdini')
	elif HOST == BLENDER:
		print('host(): Blender')
	elif HOST == C4D:
		print('host(): Cinema 4D')
