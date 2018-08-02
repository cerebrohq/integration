# -*- coding: utf-8 -*-
from tentaculo.core import capp

def todolist():
	from tentaculo.api.icerebro import db
	if db.Db().login():
		from tentaculo.gui import taskwindow
		wndParent = capp.app_window()
		wnd = taskwindow.w_taskwindow(link_mode = False, parent = wndParent)
		wnd.run()

def browser():
	from tentaculo.api.icerebro import db
	if db.Db().login():
		from tentaculo.gui import taskwindow
		wndParent = capp.app_window()
		wnd = taskwindow.w_taskwindow(link_mode = True, parent = wndParent)
		wnd.run()

def createreport():
	from tentaculo.api.icerebro import db
	if db.Db().login():
		from tentaculo.gui import sendreport
		wndParent = capp.app_window()
		wnd = sendreport.w_createReport(to_publish = False, parent = wndParent)
		wnd.run()

def publish():
	from tentaculo.api.icerebro import db
	if db.Db().login():
		from tentaculo.gui import sendreport
		wndParent = capp.app_window()
		wnd = sendreport.w_createReport(to_publish = True, parent = wndParent)
		wnd.run()

def logout():
	from tentaculo.api.icerebro import db
	if db.Db().logoff():
		from tentaculo.gui import taskwindow
		wndParent = capp.app_window()
		wnd = taskwindow.w_taskwindow(link_mode = False, parent = wndParent)
		wnd.run()

def workdir():
	from tentaculo.api.icerebro import db
	conn = db.Db()
	conn.set_work_directory()

def about():
	from tentaculo.gui import wabout
	wndParent = capp.app_window()
	wnd = wabout.w_about(parent = wndParent)
	wnd.run()

def reload():
	from tentaculo import reloadmodules
	reloadmodules.reload_modules()
