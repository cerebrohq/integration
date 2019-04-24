# -*- coding: utf-8 -*-
import sys, os, platform
# Reroute stdout & stderr if started without console
if sys.executable.endswith("pythonw.exe"):
	sys.stdout = open(os.devnull, "w")
	sys.stderr = open(os.devnull, "w")

from tentaculo.core import utils

# Define messages display
DEBUG = False
try:
	from tentaculo import debug
	DEBUG = debug.DEBUG
except ImportError:
	pass

# Host window handle
APP_HANDLE = None

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
KATANA = 70

# Host file extensions
MAYA_EXT = ['.ma', '.mb']
NUKE_EXT = ['.nk']
HOUDINI_EXT = ['.hip']
MAX_EXT = ['.max']
C4D_EXT = ['.c4d']
BLENDER_EXT = ['.blend']
KATANA_EXT = ['.katana']
HOST_EXT = []
HOST_NAME = 'Standalone'

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

try:
	import Katana
	from Katana import KatanaFile, UI4, NodegraphAPI
	HOST = KATANA
	HOST_NAME = 'katana'
	HOST_EXT = KATANA_EXT
	os.environ['QT_PREFERRED_BINDING'] = 'PyQt4'
	os.environ['QT_SIP_API_HINT'] = '1'
except ImportError:
	pass

from tentaculo import Qt

if HOST == C4D or HOST == BLENDER or HOST == STANDALONE:
	if utils.PY3:
		Qt.QtCore.QCoreApplication.addLibraryPath(os.path.join(utils.plugin_dir(), "libs3", utils.HOST_OS, "python3", "PyQt5", "plugins"))
	if not Qt.QtCore.QCoreApplication.instance():
		app = Qt.QtWidgets.QApplication(sys.argv)
		app.setWindowIcon(Qt.QtGui.QIcon(utils.getResDir("icon.png")))

QT5 = Qt.__binding__ in ["PySide2", "PyQt5"]

def set_standalone_host(hostname):
	global HOST_EXT, HOST_NAME
	if hostname is None or len(hostname) == 0: return False

	HOST_NAME = hostname

	if HOST_NAME == "revit":
		HOST_EXT = ['.rvt']
	elif HOST_NAME == "autocad":
		HOST_EXT = ['.dwg']
	elif HOST_NAME == "tbharmony":
		HOST_EXT = ['.xstage']
	else:
		HOST_EXT = ['.none']
		return False

	return True

def open_file(log, filepath, origin_path = None):
	if not os.path.exists(filepath):
		raise Exception('{0} does not exist'.format(filepath))

	if origin_path is None: origin_path = filepath

	if HOST == STANDALONE:
		from tentaculo.api import standalone
		standalone.message_function("open_file", [filepath])
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
		hou.hipFile.load(filepath.replace('\\', '/')) #, suppress_save_prompt = True)
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
	elif HOST == KATANA:
		KatanaFile.Load(filepath)

	return filepath

def close_file():
	if HOST == STANDALONE:
		from tentaculo.api import standalone
		standalone.message_function("close_file")
	elif HOST == MAYA or HOST == MAYA2:
		mc.file(new = True, force = True)
	elif HOST == NUKE:
		nuke.scriptClear()
	elif HOST == HOUDINI:
		hou.hipFile.clear(suppress_save_prompt = True)
	elif HOST == MAX:
		MaxPlus.FileManager.Reset(noPrompt = True)
	elif HOST == C4D:
		c4d.documents.CloseAllDocuments()
	elif HOST == BLENDER:
		bpy.ops.wm.read_homefile()
	elif HOST == KATANA:
		KatanaFile.New()

	return True

def create_file(log, filepath, origin_path = None):
	dir = os.path.dirname(filepath)
	if not os.path.exists(dir):
		raise Exception('{0} does not exist'.format(dir))

	if origin_path is None: origin_path = filepath

	if HOST == STANDALONE:
		from tentaculo.api import standalone
		standalone.message_function("create_file", [filepath])
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
	elif HOST == KATANA:
		KatanaFile.New()
		KatanaFile.Save(filepath)

	return filepath

def file_name(log):
	file_name = None

	if HOST == STANDALONE:
		from tentaculo.api import standalone
		file_name = standalone.message_function("file_name")[0]
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
	elif HOST == KATANA:
		file_name = NodegraphAPI.NodegraphGlobals.GetProjectAssetID()

	return file_name

def save_query(log):
	cancel = False

	if HOST == STANDALONE:
		from tentaculo.api import standalone
		cancel = standalone.message_function("save_query")[0]
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
	elif HOST == KATANA:
		if KatanaFile.IsFileDirty():
			mb = UI4.App.Application.QtGui.QMessageBox(app_window())
			mb.setText("Closing file")
			mb.setInformativeText("Save current file?")
			mb.setStandardButtons(UI4.App.Application.QtGui.QMessageBox.Yes | UI4.App.Application.QtGui.QMessageBox.No | UI4.App.Application.QtGui.QMessageBox.Cancel)
			ret = mb.exec_()
			if ret == UI4.App.Application.QtGui.QMessageBox.Yes:
				KatanaFile.Save(NodegraphAPI.NodegraphGlobals.GetProjectAssetID())
			cancel = ret == UI4.App.Application.QtGui.QMessageBox.Cancel

	return not cancel

def save_file(log, fname = None):
	if fname is None: fname = "temp"
	file_path = fname

	if HOST == STANDALONE:
		from tentaculo.api import standalone
		standalone.message_function("save_file", [file_path])
	elif HOST == MAYA or HOST == MAYA2:
		mc.file(rename = file_path)
		file_path = mc.file(save = True, type = "mayaAscii")
	elif HOST == NUKE:
		nuke.scriptSaveAs(file_path, overwrite = 1)
	elif HOST == HOUDINI:
		hou.hipFile.setName(file_path)
		hou.hipFile.save()
	elif HOST == MAX:
		MaxPlus.FileManager.Save(file_path)
	elif HOST == C4D:
		doc = c4d.documents.GetActiveDocument()
		if doc is not None:
			c4d.documents.SaveDocument(doc, str(file_path), c4d.SAVEDOCUMENTFLAGS_0, c4d.FORMAT_C4DEXPORT)
	elif HOST == BLENDER:
		bpy.ops.wm.save_mainfile(filepath = file_path)
	elif HOST == KATANA:
		KatanaFile.Save(file_path)

	return file_path

def import_file(log, fname = None, as_reference = False):
	if fname is None or not os.path.exists(fname):
		log.error("Invalid file path given for import: %s", fname)
		return False

	if HOST == STANDALONE:
		from tentaculo.api import standalone
		standalone.message_function("import_file", [fname, as_reference])
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
	elif HOST == KATANA:
		if as_reference:
			pass
		else:
			KatanaFile.Import(fname)

	return True

# Global app_window(): choose the main parent window depending on environment
def app_window():
	global APP_HANDLE

	if APP_HANDLE == None:
		if HOST == MAYA or HOST == MAYA2:
			mayaMainWindowPtr = omui.MQtUtil.mainWindow()
			mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), Qt.QtWidgets.QWidget)
			APP_HANDLE = mayaMainWindow
		elif HOST == HOUDINI:
			#hou.ui.mainQtWindow()
			APP_HANDLE = hou.qt.mainWindow()
		elif HOST == NUKE:
			for obj in Qt.QtWidgets.QApplication.topLevelWidgets():
				if (obj.inherits('QMainWindow') and	obj.metaObject().className() == 'Foundry::UI::DockMainWindow'):
					APP_HANDLE = obj
		elif HOST == MAX:
			try:
				APP_HANDLE = MaxPlus.GetQMaxMainWindow() if QT5 else MaxPlus.GetQMaxWindow()
			except:
				# Max 2016
				pass
		elif HOST == C4D:
			# TODO: No Qt windows. Mb transform main window handle?
			pass
		elif HOST == BLENDER:
			# TODO: No Qt windows. Mb transform main window handle?
			pass
		elif HOST == KATANA:
			for obj in UI4.App.Application.QtGui.qApp.topLevelWidgets():
				if type(obj).__name__ == 'KatanaWindow':
				   APP_HANDLE = obj

	return APP_HANDLE

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
	elif HOST == KATANA:
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
	elif HOST == KATANA:
		pass

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

def copyToClipboard(text = None):
	if text is None: return
	clipboard = Qt.QtWidgets.QApplication.clipboard()
	clipboard.setText(text)



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
