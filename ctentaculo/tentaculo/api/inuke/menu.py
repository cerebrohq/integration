# -*- coding: utf-8 -*-
import sys, os, time
from tentaculo.core import capp
from tentaculo.api import menu

if capp.HOST == capp.NUKE:
	import nuke
	import nukescripts

	# Setting up Nuke menu
	m = nuke.menu("Nuke").addMenu("Cerebro", index=6)
	
	m.addCommand("Todo list", lambda: menu.todolist())
	m.addCommand("Link\/Embed", lambda: menu.browser())
	m.addCommand("Save as version", lambda: menu.createreport())
	m.addCommand("Publish", lambda: menu.publish())
	m.addSeparator()
	m.addCommand("Logout", lambda: menu.logout())
	m.addSeparator()
	m.addCommand("Change working directory", lambda: menu.workdir())
	m.addSeparator()
	m.addCommand("About", lambda: menu.about())
	if capp.DEBUG is True:
		m.addCommand("Reload", lambda: menu.reload())
