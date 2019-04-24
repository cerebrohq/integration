# -*- coding: utf-8 -*-
import sys, os, time
from tentaculo.core import capp
import tentaculo.api.menu as tentaculomenu

if capp.HOST == capp.NUKE:
	import nuke
	import nukescripts

	# Setting up Nuke menu
	m = nuke.menu("Nuke").addMenu("Cerebro", index=6)
	
	m.addCommand("Todo list", lambda: tentaculomenu.todolist())
	m.addCommand("Link\/Embed", lambda: tentaculomenu.browser())
	m.addCommand("Save as version", lambda: tentaculomenu.createreport())
	m.addCommand("Publish", lambda: tentaculomenu.publish())
	m.addSeparator()
	m.addCommand("Logout", lambda: tentaculomenu.logout())
	m.addSeparator()
	m.addCommand("Change working directory", lambda: tentaculomenu.workdir())
	m.addSeparator()
	m.addCommand("About", lambda: tentaculomenu.about())
	if capp.DEBUG is True:
		m.addCommand("Reload", lambda: tentaculomenu.reload())
