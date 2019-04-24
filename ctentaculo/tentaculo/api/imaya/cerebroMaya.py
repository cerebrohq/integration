# -*- coding: utf-8 -*-
import sys, os, time
from tentaculo.core import capp
from tentaculo.api import menu

if capp.HOST == capp.MAYA:
	import maya.cmds as mc
	import maya.mel as mel
	import pymel.core as pm
	from shiboken import wrapInstance
	from maya import OpenMayaUI as omui
	from maya import OpenMaya as om

if capp.HOST == capp.MAYA2:
	import maya.cmds as mc
	import maya.mel as mel
	import pymel.core as pm
	from shiboken2 import wrapInstance
	from maya import OpenMayaUI as omui
	from maya import OpenMaya as om

def init():
	if capp.HOST == capp.MAYA or capp.HOST == capp.MAYA2:
		if pm.about(b=1):
			return
		cm = 'cerebroMenu1'
		for tmp in pm.lsUI(type='menu'):
			if cm in tmp:
				pm.deleteUI(tmp)

		root = pm.menu(cm, label='Cerebro', parent='MayaWindow', tearOff=True )
		pm.menuItem('cerebroTodoListMenu', label='Todo list', parent=root, image='', c=lambda *args: menu.todolist())
		pm.menuItem('cerebroBrowserMenu', label='Link/Embed', parent=root, image='', c=lambda *args: menu.browser())
		pm.menuItem('cerebroCreateReportNewMenu', label='Save as version', parent=root, image='', c=lambda *args: menu.createreport())
		pm.menuItem('cerebroPublishMenu', label='Publish', parent=root, image='', c=lambda *args: menu.publish())
		#pm.menuItem('cerebroVersionMenu', label='Add version', parent=root, image='', c=lambda *args: menu.version_silent())
		pm.menuItem('cerebroSep2', parent=root, divider=True)
		pm.menuItem('cerebroLogoutMenu', label='Logout', parent=root, image='', c=lambda *args: menu.logout())
		pm.menuItem('cerebroSep3', parent=root, divider=True)
		pm.menuItem('cerebroChangeWorkDir', label='Change working directory', parent=root, image='', c=lambda *args: menu.workdir())
		pm.menuItem('cerebroSep4', parent=root, divider=True)
		pm.menuItem('cerebroOpenFolder', label='Open task folder', parent=root, image='', c=lambda *args: menu.open_folder())
		pm.menuItem('cerebroOpenCerebro', label='Open task in Cerebro', parent=root, image='', c=lambda *args: menu.open_cerebro())
		pm.menuItem('cerebroSep5', parent=root, divider=True)
		pm.menuItem('cerebroShowVer', label='About', parent=root, image='', c=lambda *args: menu.about())
		if capp.DEBUG is True:
			m_reload = pm.menuItem('cerebroReload',    label='Reload', parent=root, image='', c=lambda *args: menu.reload())
