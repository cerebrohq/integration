# -*- coding: utf-8 -*-
import cerebro, sys, os

if not hasattr(sys, 'argv'):
    sys.argv  = ['']

dn = os.path.normpath(os.path.dirname(__file__))
if not dn in sys.path:
	sys.path.append(dn)

from tentaculo.core import utils, jsonio
from tentaculo.api.icerebro import db

def cerebro_message(text):
	cerebro.gui.information_box("Cerebro Tentaculo", text)

def connect_db():
	conn = db.Db()

	if not conn.client_login():
		raise Exception("Connection to database failed!")

	return conn

def browse():
	try:
		from tentaculo.core import config
		db = connect_db()
		conf = config.Config()
		task_data = cerebro.core.current_task().data()

		task = db.task(task_data[cerebro.aclasses.Task.DATA_ID])
		task_paths = conf.translate(task)
		if task_paths is not None:
			open_path = task_paths["publish"] if len(task_paths.get("publish", "")) > 0 else task_paths.get("version", None)
			opened = utils.show_dir(open_path)
			if not opened:
				cerebro_message("Task folder does not exist!")
		else:
			cerebro_message("Task translation failed!")

	except Exception as e:
		cerebro_message(repr(e))

def make_dirs():
	# Config lookup keys
	path_list = ["version", "publish", "local"]
	try:
		from tentaculo.core import config
		db = connect_db()
		conf = config.Config()

		# Additional config file for browse operations
		browse_cfg = jsonio.read(os.path.join(utils.plugin_dir(), "browse_config.json"))
		ts_cfg = []

		for val in browse_cfg.get("task_structure", []):
			try:
				valid = [ i for i in val.get("structure", []) if i.get("root", None) in path_list and i.get("dirs", None) is not None ]
			except AttributeError as e:
				raise AttributeError("Invalid structure value for [{0}, {1}]. {2}".format(
					val.get("folder_path", "{no path}"), val.get("task_activity", "{no activity}"), repr(e)))

			if len(valid) > 0:
				ts_cfg.append({
					"folder_path": val.get("folder_path", ""),
					"task_activity": val.get("task_activity", ""),
					"structure": valid
					})
		
		# Count number of folders created and errors
		nsuccess, nerror = 0, 0

		cerebro_selected = cerebro.core.selected_tasks()
		for cerebro_task in cerebro_selected:
			# Get active task data from Cerebro
			#cerebro_task = cerebro.core.current_task()
			cerebro_task_data = cerebro_task.data()

			# Query all child tasks
			prj_ids = '{' + str(cerebro_task_data[cerebro.aclasses.Task.DATA_PROJECT_ID]) + '}'

			query_text = "t.flags & 0000001 = 0"
			query_text += " and (\"taskFlags\"(t.uid, get_usid()) & 4294967296) = 0"
			query_text += " and (lower(t.cc_url) like lower('%{0}%'))".format(cerebro_task.parent_url() + cerebro_task.name())
			tasks_list = [ t[0] for t in db.db.execute("select * from \"search_Tasks\"(%s::bigint[], ''::text, %s::text, 1000);", prj_ids , query_text) ]
		
			# Add current task if has not children 
			if len(tasks_list) == 0:
				tasks_list.append(cerebro_task_data[cerebro.aclasses.Task.DATA_ID])

			tsks = db.db.tasks(tasks_list)
			db.update_tasks(tsks)

			for t in tasks_list:
				task = db.task(t)
				task_paths = conf.translate(task)
				if task_paths is not None:
					# Create config-based folder structure
					for p in path_list:
						path = task_paths.get(p, None)
						if path is not None and not os.path.exists(path):
							os.makedirs(path)
							nsuccess += 1

					# Create additional folder structure
					task_parts = [p for p in (task["path"] + task["name"]).split('/') if len(p) > 0]
					task_path = '/'.join(task_parts)
					# Config specifity
					spec = {}
					for val in ts_cfg:
						activity, folder = val["task_activity"], val["folder_path"]
						folder = folder[1:] if folder.startswith('/') else folder
						# Path substitute
						for i, p in enumerate(task_parts):
							folder = folder.replace(r"$(url[{0}])".format(i), p)

						if (len(folder) == 0 or task_path.startswith(folder)) and (len(activity) == 0 or task["activity"] == activity):
							for ts in val["structure"]:
								if task_paths.get(ts["root"], None) is not None:
									spec[len([ i for i in folder.replace('\\', '/').split('/') if len(i) > 0 ]) + (1 if len(activity) > 0 else 0)] = ts

					if len(spec) > 0:
						ts = spec[max(spec)]
						for p in ts["dirs"] if isinstance(ts["dirs"], list) else [ts["dirs"]]:
							path = os.path.join(task_paths[ts["root"]], p)
							if path is not None and not os.path.exists(path):
								os.makedirs(path)
								nsuccess += 1
				else:
					nerror += 1

		if nsuccess > 0:
			cerebro_message("Successfully created {0} task(s) folders. [{1} error(s)]".format(nsuccess, nerror))
		else:
			cerebro_message("No task(s) folders created. [{0} error(s)]".format(nerror))
		
	except Exception as e:
		cerebro_message(repr(e))
