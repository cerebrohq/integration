# -*- coding: utf-8 -*-
from tentaculo.core import capp, utils
from tentaculo.Qt.QtGui import *
from tentaculo.Qt.QtCore import *
from tentaculo.Qt.QtWidgets import *

SPLASH_HANDLE = QSplashScreen(QPixmap(utils.getResDir("splash.png")))
WND_HANDLE = None

def window_close(keep_splash = False):
	global WND_HANDLE, SPLASH_HANDLE

	if not keep_splash: SPLASH_HANDLE.close()
	if WND_HANDLE is not None:
		WND_HANDLE.close()
		WND_HANDLE = None

def start_splash():
	global SPLASH_HANDLE
	SPLASH_HANDLE.showMinimized()
	SPLASH_HANDLE.showNormal()
	QApplication.processEvents()

def todolist():
	global WND_HANDLE, SPLASH_HANDLE
	from tentaculo.api.icerebro import db
	if db.Db().login():
		from tentaculo.gui import taskwindow
		window_close(True)
		WND_HANDLE = taskwindow.w_taskwindow(link_mode = False, parent = capp.app_window())
		WND_HANDLE.run()
		SPLASH_HANDLE.finish(WND_HANDLE)
		if capp.HOST == capp.STANDALONE:
			QApplication.exec_()
			WND_HANDLE.deleteLater()

def browser():
	global WND_HANDLE, SPLASH_HANDLE
	from tentaculo.api.icerebro import db
	if db.Db().login():
		from tentaculo.gui import taskwindow
		window_close(True)
		WND_HANDLE = taskwindow.w_taskwindow(link_mode = True, parent = capp.app_window())
		WND_HANDLE.run()
		SPLASH_HANDLE.finish(WND_HANDLE)
		if capp.HOST == capp.STANDALONE:
			QApplication.exec_()
			WND_HANDLE.deleteLater()

def createreport():
	global WND_HANDLE, SPLASH_HANDLE
	from tentaculo.api.icerebro import db
	if db.Db().login():
		from tentaculo.gui import sendreport
		window_close(True)
		WND_HANDLE = sendreport.w_createReport(to_publish = False, parent = capp.app_window())
		WND_HANDLE.run()
		SPLASH_HANDLE.finish(WND_HANDLE)
		if capp.HOST == capp.STANDALONE:
			QApplication.exec_()
			WND_HANDLE.deleteLater()

def publish():
	global WND_HANDLE, SPLASH_HANDLE
	from tentaculo.api.icerebro import db
	if db.Db().login():
		from tentaculo.gui import sendreport
		window_close(True)
		WND_HANDLE = sendreport.w_createReport(to_publish = True, parent = capp.app_window())
		WND_HANDLE.run()
		SPLASH_HANDLE.finish(WND_HANDLE)
		if capp.HOST == capp.STANDALONE:
			QApplication.exec_()
			WND_HANDLE.deleteLater()

def version_silent():
	from tentaculo.core import fmanager
	from tentaculo.gui import wapp
	man = fmanager.FManager()
	res = man.version_silent()
	if res is None:
		wapp.error("Cannot determine task ID. Please start working on a task to create local version.")
	else:
		wapp.info("Current file is saved as new version: {}".format(res))

def open_folder():
	from tentaculo.core import fmanager
	from tentaculo.gui import wapp
	man = fmanager.FManager()
	if not man.open_task_folder():
		wapp.error("Cannot determine task ID. Please start working on a task to create local version.")

def open_cerebro():
	from tentaculo.core import fmanager
	from tentaculo.gui import wapp
	man = fmanager.FManager()
	if not man.open_task_cerebro():
		wapp.error("Cannot determine task ID. Please start working on a task to create local version.")

def logout():
	global WND_HANDLE, SPLASH_HANDLE
	from tentaculo.api.icerebro import db
	if db.Db().logoff():
		from tentaculo.gui import taskwindow
		window_close(True)
		WND_HANDLE = taskwindow.w_taskwindow(link_mode = False, parent = capp.app_window())
		WND_HANDLE.run()
		SPLASH_HANDLE.finish(WND_HANDLE)
		if capp.HOST == capp.STANDALONE:
			QApplication.exec_()
			WND_HANDLE.deleteLater()

def workdir():
	from tentaculo.api.icerebro import db
	conn = db.Db()
	conn.set_work_directory()

def about():
	from tentaculo.gui import wabout
	wndParent = capp.app_window()
	wnd = wabout.w_about(parent = wndParent)
	wnd.run()
	if capp.HOST == capp.STANDALONE:
		wnd.deleteLater()

def reload():
	from tentaculo import reloadmodules
	reloadmodules.reload_modules()
