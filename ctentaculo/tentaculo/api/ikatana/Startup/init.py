# -*- coding: utf-8 -*-

from tentaculo.core import capp

def init_menu(objectHash = None):
	from tentaculo.api import menu
	from tentaculo.core import capp
	
	if capp.HOST == capp.KATANA:
		import Katana
		from Katana import UI4
		from UI4.App.Application import QtGui

		layoutsMenus = [x for x in QtGui.qApp.topLevelWidgets() if type(x).__name__ == 'LayoutsMenu']
		if len(layoutsMenus) == 1:
			main_menu = layoutsMenus[0].parent()
			
			Katana.CEREBRO_MENU = dict()
			cerebro_menu = QtGui.QMenu('Cerebro', main_menu)
			Katana.CEREBRO_MENU['/Main/Cerebro'] = cerebro_menu
			main_menu.addMenu(cerebro_menu)
			
			cerebro_menu.addAction('Todo list', menu.todolist)
			cerebro_menu.addAction('Link/Embed', menu.browser)
			cerebro_menu.addAction('Save as version', menu.createreport)
			cerebro_menu.addAction('Publish', menu.publish)
			cerebro_menu.addSeparator()
			cerebro_menu.addAction('Logout', menu.logout)
			cerebro_menu.addSeparator()
			cerebro_menu.addAction('Change working directory', menu.workdir)
			cerebro_menu.addSeparator()
			cerebro_menu.addAction('About', menu.about)

if capp.HOST == capp.KATANA:
	from Katana import Callbacks
	Callbacks.addCallback(Callbacks.Type.onStartupComplete, init_menu)
