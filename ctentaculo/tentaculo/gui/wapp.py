# -*- coding: utf-8 -*-

from tentaculo.core import capp, clogger
from tentaculo.gui import style
from tentaculo.Qt.QtWidgets import *

default_title = 'Cerebro Tentaculo'

def error(message, title = default_title):
	clogger.CLogger().log.error(message, exc_info=1)
	QMessageBox.critical(capp.app_window(), title, message)

def info(message, title = default_title):
	clogger.CLogger().log.info(message)
	QMessageBox.information(capp.app_window(), title, message)

def warning(message, title = default_title):
	clogger.CLogger().log.warning(message)
	QMessageBox.warning(capp.app_window(), title, message)

def question(message, title = default_title):	
	clogger.CLogger().log.info('Question: %s', message,)	
	res = QMessageBox.question(capp.app_window(), title, message)	
	clogger.CLogger().log.info('Answer: %s', res)	
	return res == QMessageBox.Yes

def string(request, items, editable, title = default_title):
	clogger.CLogger().log.info('String request: %s', request)
	res = u""
	input = QInputDialog.getItem(capp.app_window(), title, request, items, 0, editable)
	if input[1]: res = input[0]
	clogger.CLogger().log.info('Answer: %s', res)
	return res

def directory(title, start_dir = None):	
	dir = QFileDialog.getExistingDirectory(capp.app_window(), title, start_dir)
	#clogger.CLogger().log.info('Save directory selected: %s', dir)
	return dir

def file(title, start_dir = None):
	res = None
	dir = QFileDialog.getOpenFileNames(capp.app_window(), title, start_dir)
	if isinstance(dir, tuple):
		res = dir[0] if len(dir[0]) > 0 else None
	else:
		res = dir if len(dir) > 0 else None
	return res

def menu(task, pos_global, option_list, menu_name, extra_args = {}):
	from tentaculo.core import fmanager

	ret = None

	fman = fmanager.FManager()
	styler = style.Styler()
	menu = QMenu()
	
	styler.initStyle(menu)
	extra_args["option_list"] = [ {"text": val, "index": i} for i, val in enumerate(option_list) ]
	extra_options = fman.gui_processor(task, menu_name, extra_args)
	if extra_options[1] and len(extra_options[0]) > 0:
		for opt in extra_options[0]:
			extra_args["option_list"].insert(int(opt.get("index", 0)), opt)
		for i in range(len(extra_args["option_list"])):
			extra_args["option_list"][i]["index"] = i

	action_list = []
	for opt in extra_args["option_list"]:
		if opt["text"] is None:
			menu.addSeparator()
			action_list.append(None)
		else:
			action = menu.addAction(opt["text"])
			action_list.append(action)

	action_selected = menu.exec_(pos_global)
	if action_selected is not None and action_selected in action_list:
		ret = action_selected.text()
		if ret not in option_list:
			extra_args["option"] = ret
			fman.gui_processor(task, "{}_execute".format(menu_name), extra_args, extra_args["option_list"][action_list.index(action_selected)])

	return ret