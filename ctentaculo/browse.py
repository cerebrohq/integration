# -*- coding: utf-8 -*-

import cerebro
import os
from ctentaculo.client import site_config
from ctentaculo.client import core
from ctentaculo.client import py_cerebro

conf = 'path_config'
host = 'db.cerebrohq.com'
port =  45432

def connect_db():
	db = py_cerebro.database.Database(host, port)

	if db.connect_from_cerebro_client() != 0:
		raise Exception('Connection to database failed!')

	return db

def cur_task_name():
	task = cerebro.core.current_task()

	return task.parent_url() + task.name()	

def get_dict(val):
	ret_val = None
	config = site_config.Config(conf)
	dict = config.translate(cur_task_name())

	if not dict is None:
		if val in dict.keys():
			ret_val = dict.get(val)
		else:
			cerebro.gui.critical_box('Dict Error', 'Value "' + val + '" not found in dictionary!')

	return ret_val

def browse():
	ver = get_dict('version')

	if not ver is None: # and os.path.exists(ver)
		host = core.hostapp.getHost()

		if host == 'windows':
			os.system('explorer /select,"' + os.path.normpath(ver) + '"')
		elif host == 'linux':
			os.system('xdg-open "%s"' % ver)
		elif host == 'macos':
			os.system('open "%s"' % ver)
	else:
		cerebro.gui.critical_box('Path Error', 'Path "' + str(ver) + '" not found!')

def make_dirs():
	db = connect_db()

	prj_ids = '{' + str(cerebro.core.current_task().data()[cerebro.aclasses.Task.DATA_PROJECT_ID]) + '}'

	query_text = "t.flags & 0000001 = 0"
	query_text += " and (\"taskFlags\"(t.uid, get_usid()) & 4294967296) = 0"
	query_text += " and (lower(t.cc_url) like lower('%{0}%'))".format(cur_task_name())
	tasks_list = db.execute("select * from \"search_Tasks\"(%s::bigint[], ''::text, %s::text, 1000);", prj_ids , query_text)

	id_tasks_list = []
	for id in tasks_list:
		id_tasks_list.append(id[0])

	tasks = db.tasks(id_tasks_list)

	config = site_config.Config(conf)
	for task in tasks:
		dict = config.translate(task[py_cerebro.dbtypes.TASK_DATA_PARENT_URL] + task[py_cerebro.dbtypes.TASK_DATA_NAME], task[py_cerebro.dbtypes.TASK_DATA_ACTIVITY_NAME])
		config.makeFolders(dict)

	cerebro.gui.information_box('Done', 'Directories structure created!')