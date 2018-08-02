# -*- coding: utf-8 -*-
import sys, os, platform
from ctentaculo.client.core import jsonio

DEBUG = True
#DEBUG = False
def debugMsg(msg = None):
	if DEBUG is True:
		print(msg)


HOST = 0
STANDALONE = 0
MAYA = 10
MAYA2 = 11
NUKE = 20
HOUDINI = 30
BLENDER = 40
MAX = 50

MAYA_EXT = ['.ma', '.mb']
NUKE_EXT = ['.nk']
HOUDINI_EXT = ['.hip']
HOST_EXT = MAYA_EXT + NUKE_EXT + HOUDINI_EXT




# host os
def getHost():
	return platform.system().lower()

CEREBRO_APP = 'cerebro'
OS = getHost()
if OS == 'windows':
	CEREBRO_APP = 'cerebro.exe'




# icerebro directory
INST_CONFIG = 'integration_install'
def getCerebroPath(iconfig = None):
	if iconfig is None: return None
	d = jsonio.read(iconfig)
	if d is None: return None
	k = 'cerebro_path'
	if k not in d: return None
	instdir = d[k]
	cerpath = os.path.join(instdir, CEREBRO_APP)
	return cerpath




try:
	from shiboken import wrapInstance
	import maya.cmds as mc
	import maya.mel as mel
	import pymel.core as pm
	import maya.OpenMaya as om
	import maya.OpenMayaUI as omui
	HOST = MAYA
	HOST_EXT = MAYA_EXT
	os.environ['QT_PREFERRED_BINDING'] = 'PySide'
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
	os.environ['QT_PREFERRED_BINDING'] = 'PySide2'
except ImportError:
	pass

try:
	import nuke
	import nukescripts
	HOST = NUKE
	HOST_EXT = NUKE_EXT
	os.environ['QT_PREFERRED_BINDING'] = 'PySide'
except ImportError:
	pass

try:
	import hou
	HOST = HOUDINI
	HOST_EXT = HOUDINI_EXT
	os.environ['QT_PREFERRED_BINDING'] = 'PySide2'
except ImportError:
	pass

try:
	import bpy
	HOST = BLENDER
except ImportError:
	pass



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
	elif HOST == MAX:
		print('host(): 3dsmax')
