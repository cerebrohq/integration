# -*- coding: utf-8 -*-
import sys, os, platform, shutil, subprocess, tempfile, imp
import json as json

from tentaculo.core import capp, config, clogger, vfile
from tentaculo.api.icerebro import db
from tentaculo.gui import wapp

# file manager: open - save - publish
# WARNING: This is SINGLETON
class FManager(object):
	# singleton	
	__instance = None

	def __new__(cls, *args, **kwargs):
		if not isinstance(cls.__instance, cls):
			cls.__instance = super(FManager, cls).__new__(cls, *args, **kwargs)
			cls.__instance()
		return cls.__instance

	def __call__(self):
		self.init_manager()

	def init_manager(self):
		self.log = clogger.CLogger().log
		self.paths = config.Config()
		self.db = db.Db()
		
	def execute(self, func, args):
		res = None
		try:
			res = func(*args)
		except Exception as err:
			self.log.debug('EXCEPTION', exc_info=1)
			wapp.error(capp.string_unicode(str(err)))

		return res

	def view(self, task, filepath):
		return self.execute(self.z_view, (task, filepath))

	def create(self, task):
		return self.execute(self.z_create, (task,))

	def open(self, task, filepath, linked_task):
		return self.execute(self.z_open, (task, filepath, linked_task))

	def version(self, task, processdata, status, ver_thumb):
		return self.execute(self.z_verison, (task, processdata, status, ver_thumb))

	def publish(self, task, processdata, status, ver_thumb):
		return self.execute(self.z_publish, (task, processdata, status, ver_thumb))

	def link(self, task, file_path):
		return self.execute(self.z_link, (task, file_path))

	def embed(self, task, file_path):
		return self.execute(self.z_embed, (task, file_path))

	def z_format_taskdata(self, task):
		taskdata = {}
		if task is not None:
			taskdata["task_id"] = task["id"]
			taskdata["task_name"] = task["name"]
			taskdata["task_parent_id"] = task["parent"]
			taskdata["task_parent_path"] = task["path"]
			taskdata["task_activity_id"] = task["activity_id"]
			taskdata["task_activity_name"] = task["activity"]
			taskdata["task_status_id"] = task["status_id"]
			taskdata["task_status_name"] = task["status"]
			user = self.db.current_user()
			taskdata["current_user_id"] = user[0]
			taskdata["current_user_name"] = user[1]

		return taskdata

	def z_processor(self, task, function_name, function_arg):
		ret_value = function_arg
		call_made = False
		callinfo = self.paths.processorinfo(task["unid"], function_name)
		if callinfo[0] is not None and callinfo[1] is not None:
			if os.path.exists(callinfo[0]):
				module = imp.load_source('', callinfo[0])
				if hasattr(module, callinfo[1]):
					ret_value = getattr(module, callinfo[1])(self.z_format_taskdata(task), function_arg)
					call_made = True
				else:
					raise Exception("Specified function '{0}' not found in {1}".format(callinfo[1], callinfo[0]))
			else:
				raise Exception("Specified file '{0}' not found".format(callinfo[0]))

		return (ret_value, call_made)

	def z_view(self, task, filepath):
		self.log.info('Open to view file started...')
		self.log.info('Task: %s. Path file: %s', task["path"] + task["name"], filepath)
		#module = __import__('tentaculo.core.capp')
		#func = getattr(module, 'bar')

		new_filepath = None
		if capp.save_query(self.log):
			new_filepath = capp.open_file(self.log, filepath)

		if new_filepath is not None:
			self.log.info('Open to view %s file has been successfull.', new_filepath)
			return True
		else:
			self.log.info('Open to view file has been aborted.')
			return False

	def z_create(self, task):
		self.log.info('Create file started...')	
		self.log.info('Task: %s', task["path"] + task["name"])
		
		res = False
		task_paths = self.paths.translate(task)
		if task["name_editable"] or len(task["name_list"]) > 1:
			task_paths["name"] = wapp.string("Enter valid file name", task["name_list"], task["name_editable"])

		if len(task_paths["name"]) != 0:
			try:
				self.paths.set_task_filename(task["id"], task_paths["name"])
				fvers = vfile.VFile(task_paths)

				processdata = {}
				processdata["original_file_path"] = fvers.publish_path()
				processdata["local_file_path"] = fvers.local_path()

				ret = self.z_processor(task, "new_pre", processdata)
				if ret[0] is None: return False
				processdata["local_file_path"] = ret[0]["local_file_path"]
				ret = self.z_processor(task, "new_replace", processdata)

				if ret[0] is not None and not ret[1]:
					processdata["local_file_path"] = ret[0]["local_file_path"]
					if not os.path.exists(os.path.dirname(processdata["local_file_path"])):
						os.makedirs(os.path.dirname(processdata["local_file_path"]))

					if capp.save_query(self.log):
						processdata["local_file_path"] = capp.create_file(self.log, processdata["local_file_path"], processdata["original_file_path"])
						self.paths.save_task_file(task, processdata["local_file_path"])
						res = True

				self.z_processor(task, "new_post", processdata)

				if res:
					self.log.info('File %s has been successfully created.', processdata["local_file_path"])
				else:
					self.log.info('File creation has been aborted.')
			except Exception as err:
				wapp.error(capp.string_unicode(str(err)))
		else:
			self.log.warning('Valid file name is required!')
		
		return res

	def z_open(self, task, filepath, linked_task):
		self.log.info('Load file started...')		
		self.log.info('Task: %s. Path original file: %s', task["path"] + task["name"], filepath)

		orig_ext = os.path.splitext(filepath)[1]
		task_paths = self.paths.translate(task)
		fvers = vfile.VFile(task_paths, orig_ext)
		res = False

		if task["name_editable"] or len(task["name_list"]) > 1:
			custom_name = u""
			if linked_task:
				custom_name = wapp.string("Enter valid file name", task["name_list"], task["name_editable"])
			else:
				custom_name = fvers.file_name(filepath)
			if len(custom_name) > 0:
				self.paths.set_task_filename(task["id"], custom_name)
				task_paths = self.paths.translate(task)
				fvers.setConfig(task_paths, orig_ext)
			else:
				return False

		try:
			processdata = {}
			processdata["original_file_path"] = filepath
			processdata["local_file_path"] = fvers.local_path()

			ret = self.z_processor(task, "open_pre", processdata)
			if ret[0] is None: return False
			processdata["local_file_path"] = ret[0]["local_file_path"]
			ret = self.z_processor(task, "open_replace", processdata)

			if ret[0] is not None and not ret[1]:
				processdata["local_file_path"] = ret[0]["local_file_path"]
				if filepath != processdata["local_file_path"]:
					self.log.info('Copy file to working directory: %s', processdata["local_file_path"])	
					if not os.path.exists(os.path.dirname(processdata["local_file_path"])):
						os.makedirs(os.path.dirname(processdata["local_file_path"]))

					shutil.copy(filepath, processdata["local_file_path"])

				if capp.save_query(self.log):
					processdata["local_file_path"] = capp.open_file(self.log, processdata["local_file_path"], filepath)
					self.paths.save_task_file(task, processdata["local_file_path"], fvers.file_version(filepath))
					res = True

			self.z_processor(task, "open_post", processdata)

			if res:
				self.log.info('Load %s file has been successfull.', processdata["local_file_path"])
			else:
				self.log.info('Load file has been aborted.')
		except Exception as err:
			wapp.error(capp.string_unicode(str(err)))

		return res

	
	def z_verison(self, task, processdata, status, ver_thumb):
		self.log.info('Save version file started...')
		self.log.info('Task: %s', task["path"] + task["name"])
		
		new_filepath = None
		task_paths = self.paths.translate(task)

		fvers = vfile.VFile(task_paths)
		processdata["version_file_path"] = fvers.next_version_path()
		processdata["local_file_path"] = self.z_save_file(fvers)

		ret = self.z_processor(task, "version_pre", processdata)
		if ret[0] is None: return False
		for k in processdata:
			processdata[k] = ret[0][k]

		ret = self.z_processor(task, "version_replace", processdata)
		if ret[0] is not None and not ret[1]:
			for k in processdata:
				processdata[k] = ret[0][k]

			new_filepath = self.z_save_version(task, fvers, processdata["local_file_path"], processdata["version_file_path"])

			self.log.info('Save %s version file has been successfull.', new_filepath)
			self.log.debug('New status: %s. Time: %s', status, processdata["report"]["work_time"])
			self.db.send_report(
					task["id"],
					processdata["report"]["plain_text"],
					status,
					processdata["version_file_path"],
					ver_thumb,
					processdata["report"]["work_time"],
					processdata["links"],
					processdata["attachments"]
				)

		self.z_processor(task, "version_post", processdata)

		return new_filepath

	def z_publish(self, task, processdata, status, ver_thumb):
		self.log.info('Publish file started...')
		self.log.info('Task: %s', task["path"] + task["name"])
		
		versionpath = None
		task_paths = self.paths.translate(task)

		fvers = vfile.VFile(task_paths)
		processdata["version_file_path"] = fvers.next_version_path()
		processdata["local_file_path"] = self.z_save_file(fvers)
		processdata["publish_file_path"] = fvers.publish_path()

		ret = self.z_processor(task, "publish_pre", processdata)
		if ret[0] is None: return False
		for k in processdata:
			processdata[k] = ret[0][k]

		ret = self.z_processor(task, "publish_replace", processdata)
		if ret[0] is not None and not ret[1]:
			for k in processdata:
				processdata[k] = ret[0][k]

			if processdata["publish_file_path"] is None or len(processdata["publish_file_path"]) == 0:
				raise Exception('Path to publish in empty')

			if not os.path.exists(os.path.dirname(processdata["publish_file_path"])):
				os.makedirs(os.path.dirname(processdata["publish_file_path"]))

			shutil.copy(processdata["local_file_path"], processdata["publish_file_path"])

			versionpath = self.z_save_version(task, fvers, processdata["local_file_path"], processdata["version_file_path"])
			if versionpath is None: versionpath = processdata["publish_file_path"]

			self.log.info('Publish %s file has been successfull.', processdata["publish_file_path"])
			self.log.debug('New status: %s. Time: %s', status, processdata["report"]["work_time"])
			self.db.send_report(
					task["id"],
					processdata["report"]["plain_text"],
					status,
					processdata["version_file_path"],
					ver_thumb,
					processdata["report"]["work_time"],
					processdata["links"],
					processdata["attachments"]
				)

		self.z_processor(task, "publish_post", processdata)

		return versionpath

	def z_link(self, task, file_path):
		self.log.info('Link file started...')
		self.log.info('Task: %s', task["path"] + task["name"])
		self.log.info('File path: %s', file_path)

		processdata = {}
		processdata["file_path"] = file_path
		res = False

		ret = self.z_processor(task, "link_pre", processdata)
		if ret[0] is None: return False
		processdata["file_path"] = ret[0]["file_path"]

		ret = self.z_processor(task, "link_replace", processdata)
		if ret[0] is not None and not ret[1]:
			processdata["file_path"] = ret[0]["file_path"]
			res = capp.import_file(self.log, file_path, True)

		self.z_processor(task, "link_post", processdata)

		return res

	def z_embed(self, task, file_path):
		self.log.info('Embed file started...')
		self.log.info('Task: %s', task["path"] + task["name"])
		self.log.info('File path: %s', file_path)

		processdata = {}
		processdata["file_path"] = file_path
		res = False

		ret = self.z_processor(task, "embed_pre", processdata)
		if ret[0] is None: return False
		processdata["file_path"] = ret[0]["file_path"]

		ret = self.z_processor(task, "embed_replace", processdata)
		if ret[0] is not None and not ret[1]:
			processdata["file_path"] = ret[0]["file_path"]
			res = capp.import_file(self.log, file_path, False)

		self.z_processor(task, "embed_post", processdata)

		return res

	def z_save_file(self, fvers):
		filepath = fvers.local_path()
		if not os.path.exists(os.path.dirname(filepath)):
			os.makedirs(os.path.dirname(filepath))

		filepath = capp.save_file(self.log, filepath)
		if not filepath:
			raise Exception('Save file error')

		return filepath

	def z_save_version(self, task, fvers, filepath, savepath):
		if savepath is None:
			self.log.info('Path to save version is empty')
		else:
			if not os.path.exists(os.path.dirname(savepath)):
				os.makedirs(os.path.dirname(savepath))

			if self.paths.net_mode == self.paths.MODE_LOCAL:
				shutil.copy(filepath, savepath)
				self.paths.save_task_file(task, filepath, fvers.last_number+1)
			elif self.paths.net_mode == self.paths.MODE_NETWORK:
				shutil.move(filepath, savepath)
				capp.open_file(self.log, savepath)
			
		return savepath
