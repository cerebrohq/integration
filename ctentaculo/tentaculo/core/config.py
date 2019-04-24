# -*- coding: utf-8 -*-
import sys, os, platform, shutil, re, time, subprocess, datetime

from tentaculo.core import capp, paths, jsonio, clogger, utils
from transliterate import slugify, detect_language

# WARNING: This is SINGLETON
class Config(object):
	__instance = None

	MODE_LOCAL = 0
	MODE_NETWORK = 1
	MODE_REMOTE = 2

	MODE_COPY = 0
	MODE_MOVE = 1

	def __new__(cls, *args, **kwargs):
		if not isinstance(cls.__instance, cls):
			cls.__instance = super(Config, cls).__new__(cls, *args, **kwargs)
			cls.__instance.__initialized = False
			cls.__instance()
		return cls.__instance
		
	def __call__(self):
		self.log = clogger.CLogger().log
		self.clear()

	def clear(self):
		self.netpaths = paths.Paths()

		# Mirada executable path
		self.mirada_path = None
		# Universe config
		self.config_unid = None
		self.config_pool = {}
		localcfg = jsonio.read(os.path.join(utils.plugin_dir(), "path_config.json"))
		if localcfg is not None:
			self.set_config("local", localcfg)
		# File names
		self.task_filenames = {}
		# Task -> file config
		self.source_taskfile = "taskfile_config.json"
		self.config_taskfile = {}
		# Defaults		
		self.clear_config()
		self.load_task_file()

	def clear_config(self):
		self.config_task = {}
		self.defPaths = {}
		self.roots = {}
		self.net_mode = self.MODE_NETWORK
		self.save_mode = self.MODE_COPY
		self.trans_mode = False

	def set_local_dir(self, dir):
		self.local_dir = dir

	def set_task_filename(self, task_id, filename):
		self.task_filenames[task_id] = filename

	def set_config(self, unid, cfg, force = False):
		if unid is None or (unid in self.config_pool and not force): return False
		if cfg is None or len(cfg) == 0:
			self.config_pool[unid] = None
			self.log.warning("Invalid database config data: unid - %s; cfg - %s", unid, cfg)
			return False

		self.log.info("Setting config for unid: %s", unid)

		defPaths = {}
		roots = {}
		net_mode = self.MODE_NETWORK
		save_mode = self.MODE_COPY
		trans_mode = False
		# Project paths
		project_paths = cfg["project_path"]
		for paths in project_paths:
			valid_path = self.netpaths.add_paths(paths['paths'])
			if valid_path:
				roots.setdefault((paths.get("project_name", ""), paths.get("task_activity", "")), valid_path)
			else:				
				self.log.error("Project paths not available: %s", paths["paths"])

		self.log.debug("roots %s", roots)

		# Net mode
		modes = ["local", "network"]#, "remote"]
		mode = cfg.get("net_mode", {}).get(capp.HOST_NAME, "network").lower()
		if mode in modes:
			net_mode = modes.index(mode)
			self.log.debug("net_mode is set to %s", modes[net_mode])
		else:
			if mode == "remote":
				self.log.warning("net_mode 'remote' support will be added in future versions. Using default(%s) mode", modes[net_mode])
			else:
				self.log.error("net_mode %s not recognized. Using default(%s) mode", mode, modes[net_mode])

		# Transliteration mode
		trans_mode = cfg.get("trans_mode", {}).get(capp.HOST_NAME, False)
		try:
			trans_mode = trans_mode if isinstance(trans_mode, bool) else trans_mode.lower() == "true"
		except:
			trans_mode = False

		self.log.debug('trans_mode is set to %s', trans_mode)

		# Save mode
		modes = ["copy", "move"]
		mode = cfg.get("version_save", {}).get(capp.HOST_NAME, {}).get("save_mode", "copy").lower()
		if mode in modes:
			save_mode = modes.index(mode)
			self.log.debug("save_mode is set to %s", modes[save_mode])

		# Mirada executable path
		mirada = cfg.get("mirada_path", {}).get(utils.HOST_OS, None)
		if mirada is not None and os.path.exists(mirada):
			self.mirada_path = os.path.normpath(mirada)
			self.log.info("Mirada executable path: %s", self.mirada_path)

		# Default paths
		cfgDefPaths = [item for item in cfg["file_path"] if item.get("folder_path", "") == "" and item.get("task_activity", "") == ""]
		defPaths = cfgDefPaths[0] if len(cfgDefPaths) > 0 else defPaths

		self.config_pool[unid] = (cfg, roots, defPaths, trans_mode, net_mode, save_mode)

		self.log.info("Successfully loaded config for %s.", unid)

		return True

	def select_config(self, unid):
		if self.config_unid != unid:
			self.config_unid = unid
			self.clear_config()
			unid = unid if self.config_pool.get(unid, None) is not None else "local"
			if unid in self.config_pool:
				self.config_task = self.config_pool[unid][0]
				self.roots = self.config_pool[unid][1]
				self.defPaths = self.config_pool[unid][2]
				self.trans_mode = self.config_pool[unid][3]
				self.net_mode = self.config_pool[unid][4]
				self.save_mode = self.config_pool[unid][5]

	def load_task_file(self):
		self.config_taskfile = jsonio.read(os.path.join(utils.configdir(), self.source_taskfile))

	def save_task_file(self, task, filepath, version = None):
		if task is None or filepath is None: return None

		filepath = os.path.normcase(os.path.normpath(filepath))
		if version is None:
			version = self.version_for_file(filepath)

		self.config_taskfile[filepath] = {}
		self.config_taskfile[filepath]["id"] = task["id"]
		self.config_taskfile[filepath]["version"] = version
		self.config_taskfile[filepath]["time"] = (datetime.datetime.now() - datetime.datetime.fromtimestamp(0)).total_seconds()

		jsonio.write(os.path.join(utils.configdir(), self.source_taskfile), self.config_taskfile)

	def mirada(self):
		return self.mirada_path
		
	def redirect_path(self, path):
		if path is None: return None
		return self.netpaths.redirect(path)

	def task_for_file(self, filepath):
		if filepath is None: return None
		filepath = os.path.normcase(os.path.normpath(filepath))
		conf = self.config_taskfile.get(filepath, None)
		return None if conf is None else conf["id"]

	def version_for_file(self, filepath):
		if filepath is None: return None
		filepath = os.path.normcase(os.path.normpath(filepath))
		conf = self.config_taskfile.get(filepath, None)
		return None if conf is None else conf["version"]

	def time_for_file(self, filepath):
		if filepath is None: return None
		filepath = os.path.normcase(os.path.normpath(filepath))
		conf = self.config_taskfile.get(filepath, None)
		return None if conf is None else datetime.datetime.fromtimestamp(conf["time"])
	
	def task_valid(self, task):
		if task["valid_task"] is None or task["valid_parent"] is None:
			self.translate(task)

		return [task["valid_task"], task["valid_parent"]]

	def processorinfo(self, task_unid, function_name):
		self.select_config(task_unid)
		res = (None, None)
		app_proc = self.config_task.get("processors", {}).get(capp.HOST_NAME, {}).get(function_name, None)
		if app_proc is not None:
			app_script = app_proc.get("script_path", None)
			app_func = app_proc.get("function", None)
			if app_script is not None and app_func is not None:
				app_script = os.path.normpath(app_script) if os.path.isabs(app_script) else os.path.abspath(os.path.join(utils.plugin_dir(), app_script))
				res = (app_script, app_func)

		return res

	def translate(self, task):
		task_paths = {}
		if task is None: return task_paths

		# Select config by universe ID
		self.select_config(task["unid"])
		self.log.debug('Translate task %s stared...', task["id"])

		task_path = task["path"] + task["name"]

		# Explode task path. Transliterate if enabled.
		ln = detect_language(task_path) if self.trans_mode else 'ru'
		ln = ln if ln is not None else 'ru'

		task_path_parts = [ slugify(p, ln) if self.trans_mode else p for p in task_path.split('/') if len(p) > 0 ]

		# Fill in supported variables
		string_vars = {}
		string_vars["task_name"] = task_path_parts[-1]
		string_vars["task_path"] = '/'.join(task_path_parts)
		string_vars["task_parent_name"] = '' if len(task_path_parts) < 2 else task_path_parts[-2]
		string_vars["task_parent_path"] = '/'.join(task_path_parts[:-1])
		string_vars["soft_folder"] = self.config_task.get("soft_folder", {}).get(capp.HOST_NAME, "")

		# Add path parts as URL's variables
		for i, p in enumerate(task_path_parts):
			string_vars[r"url[{0}]".format(i)] = p

		# Get root directory for current task
		curPaths = self.file_path(task)
		root = self.project_path(task_path_parts[0], task["activity"])
		self.log.debug('root %s', root)	
		if len(root) == 0:
			self.log.error('Task %s root is empty', task_path)

		paths = ["local", "publish", "version"]
		task_valid = True
		task_isparent = len(curPaths) > 0
		token = r"$(url["

		for key, url in curPaths.items():
			items = url[:] if isinstance(url, list) else [url]

			if not isinstance(url, (int, bool)) and len(url) > 0:
				for i in range(len(items)):
					keys = re.findall(r"\$\(([^/\$]+)\)", items[i])

					for k in keys:
						if not k in string_vars:
							env_var = os.environ.get(k)
							if env_var is not None:
								string_vars[k] = env_var
							else:
								self.log.error('Variable %s not evaluated', k)
								# TODO: raise error? set empty string?
								pass

					for name, var in string_vars.items():
						items[i] = items[i].replace(r"$({0})".format(name), var)

					if key in paths:
						items[i] = os.path.normpath(os.path.join(root, items[i]))
						task_isparent = task_isparent if items[i].find(token) < 0 else False

			task_paths[key] = items if isinstance(url, list) else items[0]

		# Fill name list if provided
		if isinstance(task_paths.get("name", u""), list):
			task_paths["name_list"] = task_paths.pop("name")
		else:
			task_paths["name_list"] = [task_paths.get("name", u"")]

		# Check if name is editable
		is_name_editable = curPaths.get("name_editable", False)
		try:
			task["name_editable"] = is_name_editable if isinstance(is_name_editable, bool) else is_name_editable.lower() == "true"
		except:
			task["name_editable"] = False

		# Check for custom file name ...
		custom_name = self.task_filenames.get(task["id"], '')
		if (len(custom_name) > 0 and task["name_editable"]) or len(task_paths["name_list"]) > 1:
			task_paths["name"] = custom_name
		elif len(task_paths.get("name", "")) == 0:
			file_name = capp.file_name(self.log)
			if file_name is not None and len(file_name) > 0:
				task_paths["name"] = os.path.splitext(os.path.basename(file_name))[0]

		# ... or set temp name as default
		task_paths.setdefault("name", "temp")

		# Task is valid when no URL's remain in name and paths
		task_valid = task_paths["name"].find(token) < 0 and task_isparent
		if task_valid: task_isparent = False
		task["valid_task"] = task_valid
		task["valid_parent"] = task_isparent

		# Set task publish status
		task["publish_status"] = task_paths.get("publish_status", None)

		# Set default local location
		local = task_paths["publish"] if len(task_paths.get("publish", "")) > 0 else task_paths.get("version", "")
		if self.net_mode == self.MODE_LOCAL and self.local_dir is not None:
			local = local.replace(root, self.local_dir)

		self.log.debug('Local self.local_dir: %s; local: %s', self.local_dir, local)
		task_paths.setdefault('local', os.path.normpath(local))

		# Set default values if empty
		for key in paths:
			task_paths.setdefault(key, "")

		self.log.debug('%s', task_paths)
		self.log.debug('Translate has been successfull.')

		return task_paths

	# Paths translation
	def project_path(self, proj, activity):
		activity = activity if activity is not None else ''
		proj = proj if proj is not None else ''
		path = self.roots.get((proj, activity), '')
		if path == '':
			path = self.roots.get(('', ''), '')
		return path

	def file_path(self, task):
		if task is not None:
			task_path = task["path"] + task["name"]
			task_parts = [p for p in task_path.split('/') if len(p) > 0]
			task_path = '/'.join(task_parts)

			# Config specifity
			spec = {}
			for fp in self.config_task.get("file_path", []):
				activity = fp.get("task_activity", "")
				folder = fp.get("folder_path", "")
				# Default key skip
				if len(folder) == 0 and len(activity) == 0: continue
				folder = folder[1:] if folder.startswith('/') else folder
				# Path substitute
				for i, p in enumerate(task_parts):
					folder = folder.replace(r"$(url[{0}])".format(i), p)

				if (len(folder) == 0 or task_path.startswith(folder)) and (len(activity) == 0 or task["activity"] == activity):
					depth = len([ i for i in folder.replace('\\', '/').split('/') if len(i) > 0 ])
					if not depth in spec or task["activity"] == activity:
						spec[depth] = fp

			self.log.debug('file_path specifity: %s', spec)
			return spec[max(spec)] if len(spec) > 0 else self.defPaths
		else:
			return self.defPaths
