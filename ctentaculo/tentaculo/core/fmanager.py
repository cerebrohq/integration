# -*- coding: utf-8 -*-
import sys, os, platform, shutil, subprocess, tempfile, imp, webbrowser, locale
import json as json

from tentaculo.core import capp, config, clogger, vfile, utils
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
		self.config = config.Config()
		self.db = db.Db()
		
	def execute(self, func, args):
		res = None
		try:
			res = func(*args)
		except Exception as err:
			self.log.debug('EXCEPTION', exc_info=1)
			wapp.error(utils.error_unicode(err))

		return res

	def view(self, task, filepath):
		return self.execute(self.z_view, (task, filepath))

	def create(self, task):
		return self.execute(self.z_create, (task,))

	def open(self, task, filepath, linked_task):
		return self.execute(self.z_open, (task, filepath, linked_task))

	def version(self, task, processdata, status, ver_thumb, hashtags = []):
		return self.execute(self.z_verison, (task, processdata, status, ver_thumb, hashtags))

	def version_silent(self):
		return self.execute(self.z_version_silent, set())

	def open_task_folder(self):
		return self.execute(self.z_open_task_folder, set())

	def open_task_cerebro(self):
		return self.execute(self.z_open_task_cerebro, set())

	def publish(self, task, processdata, status, ver_thumb, hashtags = [], save_current = False):
		return self.execute(self.z_publish, (task, processdata, status, ver_thumb, hashtags, save_current))

	def link(self, task_id, file_path):
		return self.execute(self.z_link, (task_id, file_path))

	def embed(self, task_id, file_path):
		return self.execute(self.z_embed, (task_id, file_path))

	def z_open_task_folder(self):
		task_id = self.config.task_for_file(capp.file_name(self.log))

		task = self.db.task(task_id)
		if task is not None:
			task_paths = self.config.translate(task)
			taskPath = task_paths["publish"] if task_paths.get("publish", None) is not None else task_paths.get("version", None)
			if taskPath is not None:
				return utils.show_dir(taskPath)

		return False

	def z_open_task_cerebro(self):
		task_id = self.config.task_for_file(capp.file_name(self.log))

		task = self.db.task(task_id)
		if task is not None:
			webbrowser.open(utils.string_unicode(r"cerebro://{0}?tid={1}").format(task["path"] + task["name"], task_id))
			return True

		return False

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
		callinfo = self.config.processorinfo(task["unid"], function_name)
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
		task_paths = self.config.translate(task)
		if task["name_editable"] or len(task_paths["name_list"]) > 1:
			task_paths["name"] = wapp.string("Enter valid file name", task_paths["name_list"], task["name_editable"])

		if len(task_paths["name"]) != 0:
			try:
				self.config.set_task_filename(task["id"], task_paths["name"])
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
						self.config.save_task_file(task, processdata["local_file_path"])
						res = True

				self.z_processor(task, "new_post", processdata)

				if res:
					self.log.info('File %s has been successfully created.', processdata["local_file_path"])
				else:
					self.log.info('File creation has been aborted.')
			except Exception as err:
				wapp.error(utils.error_unicode(err))
		else:
			self.log.warning('Valid file name is required!')
		
		return res

	def z_open(self, task, filepath, linked_task):
		self.log.info('Load file started...')		
		self.log.info('Task: %s. Path original file: %s', task["path"] + task["name"], filepath)

		orig_ext = os.path.splitext(filepath)[1]
		task_paths = self.config.translate(task)
		fvers = vfile.VFile(task_paths, orig_ext)
		res = False

		if task["name_editable"] or len(task_paths["name_list"]) > 1:
			custom_name = u""
			if linked_task:
				custom_name = wapp.string("Enter valid file name", task_paths["name_list"], task["name_editable"])
			else:
				custom_name = fvers.file_name(filepath)
			if len(custom_name) > 0:
				self.config.set_task_filename(task["id"], custom_name)
				task_paths = self.config.translate(task)
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
					self.config.save_task_file(task, processdata["local_file_path"], fvers.file_version(filepath))
					res = True

			self.z_processor(task, "open_post", processdata)

			if res:
				self.log.info('Load %s file has been successfull.', processdata["local_file_path"])
			else:
				self.log.info('Load file has been aborted.')
		except Exception as err:
			wapp.error(utils.error_unicode(err))

		return res

	def z_version_silent(self):
		self.log.info('Save silent version started...')
		new_filepath = None
		task_id = self.config.task_for_file(capp.file_name(self.log))

		if task_id is not None:
			task = self.db.task(task_id)
			task_paths = self.config.translate(task)
			fvers = vfile.VFile(task_paths)

			processdata = {"publish_file_path": u"", "report": {}, "attachments": {}, "links": {}}
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

				res = wapp.question('Do you want to continue after saving the version?', 'Version saving...')	

				new_filepath = self.z_save_version(task, fvers, processdata["local_file_path"], processdata["version_file_path"], res == False)
				self.log.info('Saved file: %s', new_filepath)

			self.z_processor(task, "version_post", processdata)
			self.db.refresh_task(task_id)

		self.log.info('Save silent version successful')
		return new_filepath
	
	def z_verison(self, task, processdata, status, ver_thumb, hashtags):
		self.log.info('Save version file started...')
		self.log.info('Task: %s', task["path"] + task["name"])
		
		changed_status = status is not None and status != task["status_id"]
		new_filepath = None
		task_paths = self.config.translate(task)

		fvers = vfile.VFile(task_paths)
		processdata["version_file_path"] = fvers.next_version_path()
		processdata["local_file_path"] = self.z_save_file(fvers)

		ret = self.z_processor(task, "version_pre", processdata)
		if ret[0] is None: return False
		for k in processdata:
			processdata[k] = ret[0][k]

		for fpath in processdata["links"]:
			if len(processdata["links"][fpath]) == 0:
				processdata["links"][fpath] = self.z_thumbnails(fpath)
		
		for fpath in processdata["attachments"]:
			if len(processdata["attachments"][fpath]) == 0:
				processdata["attachments"][fpath] = self.z_thumbnails(fpath)

		ret = self.z_processor(task, "version_replace", processdata)
		if ret[0] is not None and not ret[1]:
			for k in processdata:
				processdata[k] = ret[0][k]

			new_filepath = self.z_save_version(task, fvers, processdata["local_file_path"], processdata["version_file_path"], changed_status)

			self.log.info('Save %s version file has been successfull.', new_filepath)
			self.log.debug('New status: %s. Time: %s', status, processdata["report"]["work_time"])
			msgid = self.db.send_report(
					task["id"],
					processdata["report"]["plain_text"],
					status if changed_status else None,
					processdata["version_file_path"],
					ver_thumb,
					processdata["report"]["work_time"],
					processdata["links"],
					processdata["attachments"]
				)
			if len(hashtags):
				self.db.db.message_set_hashtags(msgid, hashtags)

		self.z_processor(task, "version_post", processdata)

		return new_filepath

	def z_publish(self, task, processdata, status, ver_thumb, hashtags, save_current):
		self.log.info('Publish file started...')
		self.log.info('Task: %s', task["path"] + task["name"])
		
		changed_status = status is not None and status != task["status_id"]
		versionpath = None
		task_paths = self.config.translate(task)

		fvers = vfile.VFile(task_paths)
		processdata["version_file_path"] = fvers.current_version_path() if save_current else fvers.next_version_path()
		processdata["local_file_path"] = self.z_save_file(fvers)
		processdata["publish_file_path"] = fvers.publish_path()

		ret = self.z_processor(task, "publish_pre", processdata)
		if ret[0] is None: return False
		for k in processdata:
			processdata[k] = ret[0][k]

		for fpath in processdata["links"]:
			if len(processdata["links"][fpath]) == 0:
				processdata["links"][fpath] = self.z_thumbnails(fpath)
		
		for fpath in processdata["attachments"]:
			if len(processdata["attachments"][fpath]) == 0:
				processdata["attachments"][fpath] = self.z_thumbnails(fpath)

		ret = self.z_processor(task, "publish_replace", processdata)
		if ret[0] is not None and not ret[1]:
			for k in processdata:
				processdata[k] = ret[0][k]

			if processdata["publish_file_path"] is None or len(processdata["publish_file_path"]) == 0:
				raise Exception('Path to publish in empty')

			if not os.path.exists(os.path.dirname(processdata["publish_file_path"])):
				os.makedirs(os.path.dirname(processdata["publish_file_path"]))

			shutil.copy(processdata["local_file_path"], processdata["publish_file_path"])

			versionpath = self.z_save_version(task, fvers, processdata["local_file_path"], processdata["version_file_path"], changed_status)
			if versionpath is None: versionpath = processdata["publish_file_path"]

			self.log.info('Publish %s file has been successfull.', processdata["publish_file_path"])
			self.log.debug('New status: %s. Time: %s', status, processdata["report"]["work_time"])
			msgid = self.db.send_report(
					task["id"],
					processdata["report"]["plain_text"],
					status if changed_status else None,
					versionpath,
					ver_thumb,
					processdata["report"]["work_time"],
					processdata["links"],
					processdata["attachments"]
				)
			if len(hashtags):
				self.db.db.message_set_hashtags(msgid, hashtags)

		self.z_processor(task, "publish_post", processdata)

		return versionpath

	def z_link(self, task_id, file_path):
		self.log.info('Link file started...')

		res = False
		task = self.db.task(task_id)
		if task is not None:
			self.log.info('Task: %s', task["path"] + task["name"])
			self.log.info('File path: %s', file_path)

			processdata = {}
			processdata["file_path"] = file_path
			processdata["task_id_src"] = task["id"]
			processdata["task_id_dst"] = self.config.task_for_file(capp.file_name(self.log))

			ret = self.z_processor(task, "link_pre", processdata)
			if ret[0] is None: return False
			processdata["file_path"] = ret[0]["file_path"]

			ret = self.z_processor(task, "link_replace", processdata)
			if ret[0] is not None and not ret[1]:
				processdata["file_path"] = ret[0]["file_path"]
				res = capp.import_file(self.log, processdata["file_path"], True)

			self.z_processor(task, "link_post", processdata)

		return res

	def z_embed(self, task_id, file_path):
		self.log.info('Embed file started...')

		res = False
		task = self.db.task(task_id)
		if task is not None:
			self.log.info('Task: %s', task["path"] + task["name"])
			self.log.info('File path: %s', file_path)

			processdata = {}
			processdata["file_path"] = file_path
			processdata["task_id_src"] = task["id"]
			processdata["task_id_dst"] = self.config.task_for_file(capp.file_name(self.log))

			ret = self.z_processor(task, "embed_pre", processdata)
			if ret[0] is None: return False
			processdata["file_path"] = ret[0]["file_path"]

			ret = self.z_processor(task, "embed_replace", processdata)
			if ret[0] is not None and not ret[1]:
				processdata["file_path"] = ret[0]["file_path"]
				res = capp.import_file(self.log, processdata["file_path"], False)

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

	def z_save_version(self, task, fvers, filepath, savepath, to_move):
		if savepath is None:
			self.log.info('Path to save version is empty')
		else:
			if not os.path.exists(os.path.dirname(savepath)):
				os.makedirs(os.path.dirname(savepath))
			
			if (self.config.net_mode == self.config.MODE_NETWORK and to_move) or self.config.save_mode == self.config.MODE_MOVE:
				shutil.move(filepath, savepath)
				#capp.open_file(self.log, savepath)
				capp.close_file()
				#self.config.save_task_file(task, savepath, fvers.last_number+1)
			else:
				shutil.copy(filepath, savepath)
				self.config.save_task_file(task, filepath, fvers.last_number+1)
			# TODO: Remote option
			
		return savepath

	def z_thumbnails(self, fpath):
		tmp_dir = os.path.normpath(utils.tempdir())
		mp = self.config.mirada()
		thumbs = []
		if mp is not None and os.path.isfile(fpath):
			self.log.info("Generating thumbnails via Mirada for file: %s", fpath)
			if not utils.PY3:
				mp, fpath = utils.string_unicode(mp).encode(locale.getpreferredencoding()), utils.string_unicode(fpath).encode(locale.getpreferredencoding())
			subprocess.call('"{0}" "{1}" --mode thumbstandalone --temp "{2}"'.format(mp, fpath, tmp_dir))
			fname = os.path.basename(fpath)
			thumbs = [os.path.normpath(os.path.join(tmp_dir, t)) for t in os.listdir(tmp_dir) if t.startswith(fname)]
			if not utils.PY3:
				thumbs = [unicode(t.decode(locale.getpreferredencoding())) for t in thumbs]
			self.log.debug("Mirada generated: %s", thumbs)

		return thumbs
