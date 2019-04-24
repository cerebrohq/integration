# -*- coding: utf-8 -*-

from tentaculo.core import capp, clogger
from tentaculo.Qt.QtWidgets import *

default_title = 'Cerebro Tentaculo'

def error(message, title = default_title):
	clogger.CLogger().log.error(message)
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
	return res == QMessageBox.StandardButton.Yes

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