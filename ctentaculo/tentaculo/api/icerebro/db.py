# -*- coding: utf-8 -*-
import os, time, datetime, base64, copy, locale, threading

# Ensure libs3 are in sys.path
from tentaculo.core import capp, utils

try:
	from pycerebro import dbtypes, database, cclib
except:
	try:
		from py_cerebro import dbtypes, database, cclib
	except:
		from py_cerebro2 import dbtypes, database, cclib

from tentaculo.core import jsonio, clogger, config, vfile
from tentaculo.gui import wapp, wlogin

from tentaculo.Qt.QtWidgets import QAction
from tentaculo.Qt.QtCore import QObject, Signal

from tentaculo.api.icerebro import cargo
from tentaculo.api import menu

CACHE_TIMEOUT = 60
CACHE_TIMEOUT_RARE = 60 * 10

# QObject helper class
class DbHelper(QObject):
	task_changed = Signal(str)

	def change_task(self, task_id):
		if task_id is not None:
			self.task_changed.emit(str(task_id))

# common db utility class
# WARNING: This is SINGLETON
class Db(object):

	__slots__ = ('lock_cache', 'lock_execute', 'log', 'config', 'db', 'login_action', 'connected', 'forbid_client',
			  'cargo', 'current_parent', 'allocated', 'tree', 'links', 'alltasks', 'unid_by_prjid', 'ts_allocated',
			  'ts_browser', 'ts_links', 'current_acc', 'user_id', 'user_name', 'users', 'statuses', 'user_dir',
			  'cfg', 'event_stop', 'thread', 'fman', 'tasks_requested', 'cache_status', 'object', '__weakref__')

	# singleton
	__instance = None

	def __new__(cls, *args, **kwargs):
		if not isinstance(cls.__instance, cls):
			cls.__instance = super(Db, cls).__new__(cls, *args, **kwargs)
			cls.__instance()
		return cls.__instance

	def __del__(self):
		self.event_stop.set()
		self.object.deleteLater()
		self.thread.join()

	def __call__(self):
		self.lock_cache = threading.RLock()
		self.lock_execute = threading.Lock()
		self.event_stop = threading.Event()
		self.thread = threading.Thread(target=self.thread_load, args=())
		self.log = clogger.CLogger().log
		self.config = config.Config()
		self.db = database.Database()
		self.object = DbHelper()

		self.login_action = QAction(None)
		self.login_action.triggered.connect(self.bad_client)

		self.load_config()
		self.disconnect()

		self.thread.start()

	# full clear with 'disconnect'
	def disconnect(self, forbid_client = False):
		self.connected = False
		self.forbid_client = forbid_client
		self.cargo = None
		self.current_parent = 0
		self.clear_profile()
		self.clear_data()
		
	def clear_data(self):
		with self.lock_cache:
			self.allocated = set()
			self.tree = {}
			self.links = {}
			self.alltasks = {}
			self.unid_by_prjid = {}
			self.tasks_requested = []
			self.cache_status = {}

			self.ts_allocated = 0
			self.ts_browser = 0
			self.ts_links = 0

	def thread_load(self):
		from tentaculo.core import fmanager
		self.fman = fmanager.FManager()

		while not self.event_stop.is_set():
			while True:
				if self.event_stop.is_set(): break

				with self.lock_cache:
					if len(self.tasks_requested) == 0: break
					task_id = self.tasks_requested.pop()
					task = self.alltasks.get(task_id, {})
					thumb_hash = task.get("thumb_hashes", None)
					task_ind = task.get("indicator", "")
				
				task_changed = False
				# Thumb
				if thumb_hash is not None:
					thumb = None
					tmp = thumb_hash.split(',')
					hashes = [tmp[x] if len(tmp) > x and len(tmp[x]) > 0 else None for x in range(6)]
					hashes = hashes[0:2] + hashes[3:5]

					for h in reversed(hashes):
						thumb = self.cargo.file(h)
						if thumb is not None:
							break

					if thumb is not None:
						task_changed = True
						with self.lock_cache:
							if task_id in self.alltasks:
								self.alltasks[task_id]["thumbnail"] = thumb
				# Indicator
				if task_ind is None:
					indicator_color = self.fman.gui_processor(task, "indicator_task", None)
					if indicator_color is not None and indicator_color[0] is not None:
						task_changed = True
						with self.lock_cache:
							if task_id in self.alltasks:
								self.alltasks[task_id]["indicator"] = indicator_color[0]
				# Set task updated
				if task_changed:
					self.object.change_task(task_id)

			self.event_stop.wait(1)

	def clear_profile(self):
		self.current_acc = None
		self.user_id = None
		self.user_name = u''
		self.users = None
		self.statuses = None
		self.user_dir = None

	def set_profile(self, acc):
		self.user_id = self.db.current_user_id()
		self.current_acc = acc
			
		if self.current_acc.get('login', '') == '':
			lg = self.db.execute('select * from "getUserLogin_byID"(%s)', self.user_id)
			self.current_acc['login'] = lg[0][0]

		self.current_acc.update({'id': self.user_id})
		self.users = self.db.users()
		self.statuses = self.db.statuses()
		for u in self.users:
			id = int(u[dbtypes.USER_DATA_ID])
			if id == self.user_id:
				self.user_name = utils.string_unicode(u[dbtypes.USER_DATA_FULL_NAME])
				break

		self.log.debug('User id: %s', self.user_id)
		self.log.info('User name: %s', self.user_name)

		self.user_dir = self.current_acc.get('savepath', '')
		if not os.path.exists(self.user_dir):
			self.user_dir = self.select_work_directory()
			self.current_acc.update({'savepath': self.user_dir})
		
		self.config.set_local_dir(self.user_dir)
		self.log.info('Save directory: %s', self.user_dir)
				

	def select_work_directory(self):
		dir = None
		doc_dir = utils.homedir()
		if os.path.exists(doc_dir):
			dir = doc_dir
		else:
			dir = wapp.directory('Select woking directory')

		if dir is None or not os.path.exists(dir):
			dir = os.path.join(utils.tempdir(), capp.HOST_NAME)
			self.log.warning('Save directory not selected. We will take the temporary path to woking directory: %s', dir)
		
		return dir

	def set_work_directory(self):
		if not self.connected: return None

		self.log.info('Set woking directory started...')

		dir = wapp.directory('Select woking directory', self.user_dir)
		if dir:
			self.user_dir = dir
			self.current_acc.update({'savepath': self.user_dir})
			self.config.set_local_dir(self.user_dir)
			self.save_config()
			self.log.info('Set %s has been successfully.', self.user_dir)

	def at_logon(self, account):
		
		try:
			self.cargo = cargo.Cargo(self.log)
			self.cargo.init_host(self.db)
		except Exception as err:
			wapp.error(utils.error_unicode(err))

		self.set_profile(account)
		self.save_config()
	
	def logoff(self):
		self.log.info('Logout user %s', self.user_name)
		self.disconnect()
		MAKE_DELETE_WINDOWS = None
		acc = self.login_to(self.account())
		if acc:
			self.connected = True
			self.at_logon(acc)
			self.log.info('Login %s has been successfully.', self.user_name)
			return True

		return False

	def bad_client(self):
		menu.window_close()
		#wapp.error("Your client session has expired. Connect using credentials.")
		self.login()

	def login(self):

		if self.connected: return True

		self.log.info('Auto-login started...')
		
		acc = self.account()
		
		connect_url = acc.get('url', '')
		self.log.info('Connection URL: %s', connect_url if len(connect_url) else 'default')
		try:
			err = 3
			if not self.forbid_client:
				menu.start_splash()
				err = self.db.connect_from_cerebro_client()
				if err == 0:
					user_id = self.db.current_user_id()
					if acc.get('id') and acc.get('id') != user_id:
						err = 1
					else:
						acc['id'] = user_id
					
			if err != 0:
				if self.cfg.get('autologin') == True and acc.get('psw'):
					menu.start_splash()
					self.db.connect(acc.get('login'), acc.get('psw'), acc.get('url', ''))
				else:
					acc = self.login_to(acc)
					if not acc:
						return False

		except Exception as err:
			self.log.debug('EXCEPTION', exc_info=1)
			wapp.error('Connection failed. Please check your login and password.\nConnect URL: {0}'.format(connect_url if len(connect_url) else 'default'))
			acc = self.login_to(acc)
			if not acc:
				return False

		self.connected = True
		self.forbid_client = False
		if not self.is_current_account(acc):
			self.at_logon(acc)
		
		self.log.info('Auto-login %s has been successfully.', self.user_name)
		return True

	def client_login(self):
		if self.connected:
			return True

		acc = self.account()
		
		#dbaddress = acc.get('address').split(':')
		connect_url = acc.get('url', '')
		self.log.info('Connection URL: %s', connect_url if len(connect_url) else 'default')

		try:
			#self.db = database.Database(dbaddress[0], dbaddress[1])
			err = self.db.connect_from_cerebro_client()
			if err == 0:
				self.connected = True
		except Exception as err:
			self.log.debug('EXCEPTION', exc_info=1)

		if self.connected and not self.is_current_account(acc):
			self.at_logon(acc)

		return self.connected


	# private: login with dialog
	def login_to(self, acc):
		menu.window_close()
		dlogin = wlogin.Wlogin(parent = capp.app_window())
		acc = dlogin.start_login(self.login_as, acc, self.cfg.get('autologin'), self.cfg.get('remember'), self.cfg.get('accounts'))
		if acc:
			self.cfg.update({'autologin': dlogin.autologin()})
			self.cfg.update({'remember': dlogin.remember()})
		
		return acc

	# private: login from dialog
	def login_as(self, acc):
		connect_url = ''
		try:
			if not self.is_current_account(acc):
				self.disconnect()
				connect_url = acc.get('url', '')
				#address = acc.get('address')
				#dbaddress = address.split(':')
				#self.db = database.Database(dbaddress[0], dbaddress[1])

			self.db.connect(acc.get('login'), acc.get('psw'), acc.get('url', ''))
			menu.start_splash()
		except Exception as err:
			self.log.debug('EXCEPTION', exc_info=1)
			wapp.error('Connection failed. Please check your login and password.\nConnect URL: {0}'.format(connect_url if len(connect_url) else 'default'))
			return False
			
		return True

	# private: get account
	def account(self):
		if self.current_acc:
			return self.current_acc

		acc = None
		accs = self.cfg.get('accounts')
		if len(accs) and self.cfg.get('lastlogin'):
			for account in accs:
				if account.get('id') == self.cfg.get('lastlogin'):
					acc = account
					break
		
		if not acc:
			acc = {}
			acc.setdefault('login', u'')
			acc.setdefault('psw', u'')
			acc.setdefault('savepath', u'')

		acc.setdefault('url', '')

		return acc

	def is_current_account(self, acc):
		return acc and self.current_acc and self.current_acc.get('url', '') == acc.get('url') and self.current_acc.get('id', '') == acc.get('id')

	def load_config(self):
		self.log.debug('Loading connection config started...')
		
		self.cfg = jsonio.read(os.path.join(utils.configdir(), '.ula'))
		self.cfg.setdefault('autologin', True)	
		self.cfg.setdefault('remember', True)
		self.cfg.setdefault('lastlogin', None)
		self.cfg.setdefault('accounts', [])

		accs = self.cfg.get('accounts')
		
		for acc in accs:
			if acc.get('psw'):
				try:
					acc["psw"] = utils.string_unicode(base64.b64decode(utils.string_byte(acc["psw"]))[:-len(acc["login"])])
				except Exception:
					acc["psw"] = u''
		

		self.log.debug('Autologin: %s, Remember: %s, Lastlogin: %s', self.cfg.get('autologin'), self.cfg.get('remember'), self.cfg.get('lastlogin')) 
		self.log.debug('Loading connection config has been successfully.')

	def save_config(self):
		self.log.debug('Save connection config started...')
		
		if self.current_acc and self.current_acc.get('id'):
			accs = self.cfg.get('accounts')
			self.cfg.update({'lastlogin': self.user_id})
			saved = False
			for index, account in enumerate(accs):
				if account.get('id') == self.user_id:
					accs[index] = self.current_acc
					if not self.cfg.get('remember'):
						accs[index]['psw'] = u''
					saved = True
					break

			if not saved:
				accs.insert(0, self.current_acc)
				if not self.cfg.get('remember'):
					accs[0]['psw'] = u''
			"""
			else:
				self.cfg.update({'lastlogin': None})
				for index, account in enumerate(accs):
					if account.get('id') == self.user_id:
						#accs.pop(index)
						accs[index]['psw'] = u''
						break
			"""
			self.cfg.update({'accounts': accs})

			save_cfg = copy.deepcopy(self.cfg)
			for acc in save_cfg["accounts"]:
				acc["psw"] = utils.string_unicode(base64.b64encode(utils.string_byte(acc["psw"] + acc["login"])))

			jsonio.write(os.path.join(utils.configdir(), '.ula'), save_cfg)

		self.log.debug('Save connection config has been successfully.')

	# private: query executed
	def execute(self, func, args):
		if self.forbid_client: return None

		with self.lock_execute:
			res = None
			try:
				res = func(*args)
			except Exception as err:
				self.log.debug('EXCEPTION', exc_info=1)
				# Client connection expired
				if "#0" in str(err):
					self.disconnect(True)
					self.login_action.trigger()
					return None
				# Try to relogin and repeat
				try:
					if self.login(): res = func(*args)
				except Exception as err:
					self.log.debug('EXCEPTION', exc_info=1)
					wapp.error(utils.error_unicode(err))

			return res

	def current_user(self):
		return (self.user_id, self.user_name)

	def set_parent(self, task_id = None):
		if task_id is None:
			task_id = self.task(self.current_parent)["parent"]
		
		if task_id == 0:
			self.current_parent = task_id
			return True

		task = self.task(task_id)
		if task is not None and task["is_folder"]:
			self.current_parent = task_id
			return True

		return False

	def tasks(self):
		return self.children_tasks(self.current_parent)

	def children_tasks(self, parent_id):
		task_list = None
		if self.tree.get(parent_id, None) is None or time.time() - self.ts_browser > CACHE_TIMEOUT_RARE:
			self.execute(self.z_tasks, (parent_id,))

		children = self.tree.get(parent_id, None)
		if children is not None:
			task_list = { task_id: self.alltasks[task_id] for task_id in children }

		return task_list

	def linked_tasks(self, task_id):
		task_list = None
		if self.links.get(task_id, None) is None or time.time() - self.ts_links > CACHE_TIMEOUT_RARE:
			self.execute(self.z_linked, (task_id,))

		linked = self.links.get(task_id, None)
		if linked is not None:
			task_list = { task_id: self.alltasks[task_id] for task_id in linked }

		return task_list

	def allocated_tasks(self, showComplete = False):
		if len(self.allocated) == 0 or time.time() - self.ts_allocated > CACHE_TIMEOUT:
			self.execute(self.z_allocated_tasks, (showComplete,))

		todo = { task_id : self.alltasks[task_id] for task_id in self.allocated }

		return todo

	def task_files(self, task_id):
		if task_id is None: return None

		task = self.task(task_id)
		if task is not None:
			files = task.get("files", None)
			if files is None:
				self.execute(self.z_task_files, (task_id,))

			return task.get("files", {})
		return {}

	def task_statuses(self, task_id):
		return self.execute(self.z_task_statuses, (task_id,))

	def set_work_status(self, task_id):
		return self.execute(self.z_set_work_status, (task_id,))

	def send_report(self, taskid, text, status, ver_file, ver_thumb, work_time = 0, links = {}, attachments = {}):
		return self.execute(self.z_send_report, (taskid, text, status, ver_file, ver_thumb, work_time, links, attachments))

	def send_message(self, taskid, text, links = {}, attachments = {}):
		return self.execute(self.z_send_message, (taskid, text, links, attachments))

	def refresh(self):
		self.clear_data()
		self.allocated_tasks()
		self.tasks()

	def refresh_task(self, task_id):
		if task_id is None: return None

		self.alltasks.pop(task_id, None)

		return self.task(task_id)
		
	def task(self, task_id, runAsync = False):
		if task_id is None: return None
		
		tsk = self.alltasks.get(task_id, None)
		if not runAsync and (tsk is None or time.time() - tsk["last_update"] > CACHE_TIMEOUT):
			self.execute(self.z_task, (task_id,))

		return self.alltasks.get(task_id, None)

	def current_path(self):
		path = u"/"
		if self.current_parent != 0:
			task = self.task(self.current_parent)
			if task is not None:
				if len(task["path_repr"]) == 0:
					path = task["name"]
				else:
					path = task["path"] + task["name"]
		#if len(path) > 50:
		#	path = u"..." + path[-50:]
		return path
	
	# private: 
	def z_tasks(self, parent_id):
		with self.lock_cache:
			tsks = []
			if parent_id == 0:
				tsks = self.db.root_tasks()
			else:
				tsks = self.db.task_children(parent_id)

			self.tree[parent_id] = { tsk[dbtypes.TASK_DATA_ID] for tsk in tsks if tsk is not None }
			self.update_tasks(tsks)
			
			self.ts_browser = time.time()

	def z_linked(self, task_id):
		with self.lock_cache:
			links = self.db.task_links(task_id)

			self.links[task_id] = { l[dbtypes.TASK_LINK_SRC] for l in links if l[dbtypes.TASK_LINK_DST] == task_id }
			tsks = self.db.tasks(self.links[task_id])
			self.update_tasks(tsks)

			self.ts_links = time.time()
			
	# private:
	def z_task(self, task_id):
		with self.lock_cache:
			task = self.db.task(task_id)
			self.update_tasks([task])

	# private: 
	def z_allocated_tasks(self, showComplete = False):
		with self.lock_cache:
			db_tasks = self.db.to_do_task_list(self.user_id, showComplete)

			if len(self.config.status_list) > 0:
				statuses_set = set([ st[dbtypes.STATUS_DATA_ID] for st in self.statuses if st[dbtypes.STATUS_DATA_NAME] is not None and st[dbtypes.STATUS_DATA_NAME].lower() in self.config.status_list ])
				tasks = [ task for task in db_tasks if task[dbtypes.TASK_DATA_CC_STATUS] in statuses_set ]
			else:
				# Complete statuses
				statuses_set = set([ st[dbtypes.STATUS_DATA_ID] for st in self.statuses if cclib.has_flag(st[dbtypes.STATUS_DATA_FLAGS], dbtypes.STATUS_FLAG_WORK_STOPPED) ])
				tasks = [ task for task in db_tasks if showComplete or task[dbtypes.TASK_DATA_CC_STATUS] not in statuses_set ]

			self.allocated = { task[dbtypes.TASK_DATA_ID] for task in tasks if task is not None }

			self.update_tasks(tasks)
			self.ts_allocated = time.time()

	def z_task_statuses(self, task_id):
		rstatuses = []
		if not task_id is None:
			pstatuses = self.db.task_possible_statuses(task_id)
			pstatuses.sort(key=lambda val: val[dbtypes.STATUS_DATA_ORDER])
			rstatuses = [[utils.string_unicode(st[dbtypes.STATUS_DATA_NAME]), int(st[dbtypes.STATUS_DATA_ID]), st[dbtypes.STATUS_DATA_FLAGS]] for st in pstatuses if st[dbtypes.STATUS_DATA_NAME] is not None]
		return rstatuses

	# private: 
	def z_task_files(self, task_id):
		if task_id is None: return None
		with self.lock_cache:
			files = {}
			self.alltasks[task_id]["definition"] = ""
			self.alltasks[task_id]["messages"] = []

			task_msgs = self.db.task_messages(task_id)

			# Append local and publish files
			conf = self.config.translate(self.alltasks[task_id])
			fvers = vfile.VFile(conf)
			publish, local = fvers.publish_path(), fvers.local_path()
			local_versions = fvers.versionsAll.copy()
			last_versions = {}
			for filename, ver in local_versions.items():
				if last_versions.get(ver[0], (-1, ''))[0] < ver[1]:
					last_versions[ver[0]] = (ver[1], filename)
			last_versions = [ f[1] for f in last_versions.values() ]

			if publish is not None and os.path.exists(publish) and os.path.splitext(publish)[1] in capp.HOST_EXT:
				file = {}
				file["name"] = os.path.basename(publish)
				file["path"] = utils.np(publish)
				file["thumbnail"] = None
				file["id"] = -1
				file["version"] = None
				file["is_last_version"] = False
				file["date"] = datetime.datetime.fromtimestamp(os.path.getmtime(publish))
				file["task_id"] = task_id

				files[file["id"]] = file

			if local is not None and os.path.exists(local) and os.path.splitext(local)[1] in capp.HOST_EXT:
				file = {}
				file["name"] = os.path.basename(local)
				file["path"] = utils.np(local)
				file["thumbnail"] = None
				file["id"] = -2
				file["version"] = self.config.version_for_file(file["path"])
				file["is_last_version"] = False
				file["date"] = datetime.datetime.fromtimestamp(os.path.getmtime(local))
				file["task_id"] = task_id

				files[file["id"]] = file

			msgids = []
			for m in task_msgs:
				# message fields
				msgid = int(m[dbtypes.MESSAGE_DATA_ID])
				date = m[dbtypes.MESSAGE_DATA_CREATED]
				author = m[dbtypes.MESSAGE_DATA_CREATOR_NAME]
			
				msgids.append(msgid)

				# check uid if task is in progress
				if self.alltasks[task_id]["owned_user_id"] is not None and m[dbtypes.MESSAGE_DATA_TYPE] == dbtypes.MESSAGE_TYPE_STATUS_CHANGES:
					self.alltasks[task_id]["owned_user_id"] = int(m[dbtypes.MESSAGE_DATA_CREATOR_ID])
					self.alltasks[task_id]["uname"] = utils.string_unicode(m[dbtypes.MESSAGE_DATA_CREATOR_NAME])

				# check definition
				if m[dbtypes.MESSAGE_DATA_TYPE] == dbtypes.MESSAGE_TYPE_DEFINITION:
					msg = m[dbtypes.MESSAGE_DATA_TEXT]
					if msg is not None:
						self.alltasks[task_id]["definition"] += utils.string_unicode(msg)
						self.alltasks[task_id]["definition"] += '\n'

				if m[dbtypes.MESSAGE_DATA_TYPE] != dbtypes.MESSAGE_TYPE_DEFINITION:
					msg = m[dbtypes.MESSAGE_DATA_TEXT]
					if msg is not None:
						text = date.strftime("%d.%m.%Y")
						if not utils.PY3: text = text.decode(locale.getpreferredencoding())
						self.alltasks[task_id]["messages"].insert(0, {'author' : utils.string_unicode(author), 'date' : text, 'msg' : utils.string_unicode(msg) })
			
			dbfiles = self.db.message_attachments(set(msgids))
			link_files = { f[dbtypes.ATTACHMENT_DATA_GROUP_ID] :
				  {"id" : int(f[dbtypes.ATTACHMENT_DATA_ID]), "path" : utils.string_unicode(f[dbtypes.ATTACHMENT_DATA_FILE_NAME]), "thumbs" : [], "date" : f[dbtypes.ATTACHMENT_DATA_CREATED] }
				  for f in dbfiles if f[dbtypes.ATTACHMENT_DATA_TAG] == dbtypes.ATTACHMENT_TAG_LINK
				}

			for f in dbfiles:
				if f[dbtypes.ATTACHMENT_DATA_GROUP_ID] in link_files and f[dbtypes.ATTACHMENT_DATA_TAG] == dbtypes.ATTACHMENT_TAG_THUMB1:
					link_files[f[dbtypes.ATTACHMENT_DATA_GROUP_ID]]["thumbs"].append(f[dbtypes.ATTACHMENT_DATA_HASH])

			unique_paths = set()
			for f in link_files.values():
				file_thumb = None
				for hash_db in reversed(f["thumbs"]):
					file_thumb = self.cargo.file(hash_db)
					if file_thumb is not None:
						break

				path = f["path"]
				if os.path.splitext(path)[1] in capp.HOST_EXT:
					path = utils.np(self.config.redirect_path(path))
					if path in unique_paths: continue
					unique_paths.add(path)

					filename = os.path.basename(path)
					file = {}
					file["name"] = filename
					file["path"] = path
					file["thumbnail"] = file_thumb
					file["id"] = f["id"]
					file["version"] = fvers.file_version(path)
					file["is_last_version"] = filename in last_versions
					file["date"] = f["date"]
					file["task_id"] = task_id

					files[file["id"]] = file

			for i, (filename, ver) in enumerate(local_versions.items()):
				path = utils.np(os.path.join(fvers.path_version, filename))
				if path in unique_paths: continue
				unique_paths.add(path)

				file = {}
				file["name"] = filename
				file["path"] = path
				file["thumbnail"] = None
				file["id"] = -(3 + i)
				file["version"] = ver[1]
				file["is_last_version"] = filename in last_versions
				file["date"] = datetime.datetime.fromtimestamp(os.path.getmtime(path))
				file["task_id"] = task_id

				files[file["id"]] = file

			if not self.alltasks[task_id]["enabled_task"]:
				self.alltasks[task_id]["enabled_task"] = self.alltasks[task_id]["owned_user_id"] == self.user_id

			self.alltasks[task_id]["files"] = files
			return files

	#private
	def z_send_report(self, taskid, text, status, ver_file, ver_thumb, work_time, links, attachments):
		if taskid is None: return None

		self.log.info('Send report started...')
		messages = self.db.task_definition(taskid)
		parent_message = None
		if messages is not None:
			parent_message = messages[dbtypes.MESSAGE_DATA_ID]
		new_message_id = self.db.add_report(taskid, parent_message, text, int(work_time))

		cargo_id = self.db.execute('select * from "siteUploadList"(%s)', taskid)[0][1]
		cargo_service = self.cargo.service(cargo_id)

		if ver_file is not None and os.path.exists(ver_file):
			try:
				self.db.add_attachment(new_message_id, cargo_service, ver_file, [ver_thumb] if ver_thumb is not None else [],  '', True)
			except Exception as err:
				self.log.error(str(err), exc_info=1)

		for fpath, thumbs in links.items():
			self.db.add_attachment(new_message_id, cargo_service, fpath, thumbs,  '', True)

		for fpath, thumbs in attachments.items():
			if not os.path.exists(fpath): continue
			self.db.add_attachment(new_message_id, cargo_service, fpath, thumbs,  '', False)
			

		if status is not None:
			self.db.task_set_status(taskid, status)

		self.log.info('Send report has been successfully.')
		return new_message_id

	#private
	def z_send_message(self, taskid, text, links, attachments):
		if taskid is None: return None

		self.log.info('Send message started...')

		messages = self.db.task_definition(taskid)
		parent_message = None
		if messages is not None:
			parent_message = messages[dbtypes.MESSAGE_DATA_ID]

		new_message_id = self.db.add_note(taskid, parent_message, text)

		cargo_id = self.db.execute('select * from "siteUploadList"(%s)', taskid)[0][1]
		cargo_service = self.cargo.service(cargo_id)

		for fpath, thumbs in links.items():
			self.db.add_attachment(new_message_id, cargo_service, fpath, thumbs,  '', True)

		for fpath, thumbs in attachments.items():
			if not os.path.exists(fpath): continue
			self.db.add_attachment(new_message_id, cargo_service, fpath, thumbs,  '', False)

		self.log.info('Send message was successfull.')
		return new_message_id

	#private
	def z_set_work_status(self, task_id):
		
		if self.alltasks.get(task_id, None) is None:
			self.z_task(task_id)

		task = self.alltasks.get(task_id, None)
		if task:
			status = None
			statuses = self.z_task_statuses(task_id)
			for st in statuses:
				if cclib.has_flag(st[2], dbtypes.STATUS_FLAG_WORK_STARTED):
					if st[1] != task["status_id"]:
						status = st[1]
					break
			
			if status is not None:
				self.db.task_set_status(task_id, status)
				self.z_allocated_tasks(False)
				return True

		return False

	# private: to update tasks data
	def update_tasks(self, tasks_db):
		if tasks_db is None: return False

		# Update universe IDs
		prj_ids = { int(t[dbtypes.TASK_DATA_PROJECT_ID]) for t in tasks_db if t is not None }
		for id in prj_ids:
			if id not in self.unid_by_prjid:
				self.unid_by_prjid[id] = int(self.db.execute('select * from "getUnid_byPrj"(%s)', id)[0][0])
				if self.unid_by_prjid[id] not in self.config.config_pool:
					cfg = jsonio.parse(self.db.execute('select * from "attributeUniverse"(%s, 120)', self.unid_by_prjid[id])[0][0])
					self.config.set_config(self.unid_by_prjid[id], cfg)

		# Current timestamp
		current_time = time.time()

		for t in tasks_db:
			if t is None: continue
			task = {}
			# ID
			task["id"] = int(t[dbtypes.TASK_DATA_ID])
			# Thumb - moved to async thread
			task["thumbnail"] = None
			task["thumb_hashes"] = t[dbtypes.TASK_DATA_THUMBS]
			# Name
			task["name"] = utils.string_unicode(t[dbtypes.TASK_DATA_NAME])
			# Path
			task["path"] = utils.string_unicode(t[dbtypes.TASK_DATA_PARENT_URL])
			task["path_repr"] = task["path"][1:-1].replace("/", " > ")
			# UserID that has task in progress
			task["owned_user_id"] = None
			task["uname"] = None
			task["enabled_task"] = True
			# Status
			status_code = t[dbtypes.TASK_DATA_SELF_STATUS]
			status_name = ""
			status_xpm = None
			status_icon = None
			status_order = 0
			for st in self.statuses:
				if status_code == st[dbtypes.STATUS_DATA_ID]:
					if cclib.has_flag(st[dbtypes.STATUS_DATA_FLAGS], dbtypes.STATUS_FLAG_WORK_STARTED):
						task["owned_user_id"] = 0
						task["enabled_task"] = False
					status_name = st[dbtypes.STATUS_DATA_NAME]
					status_xpm = st[dbtypes.STATUS_DATA_ICON]
					status_order = int(st[dbtypes.STATUS_DATA_ORDER])
					if len(st) > dbtypes.STATUS_DATA_ICON_HASH:
						if st[dbtypes.STATUS_DATA_ICON_HASH] not in self.cache_status:
							self.cache_status[st[dbtypes.STATUS_DATA_ICON_HASH]] = self.cargo.file(st[dbtypes.STATUS_DATA_ICON_HASH])
						status_icon = self.cache_status[st[dbtypes.STATUS_DATA_ICON_HASH]]
					break
			if status_name is None: status_name = ""
			task["status"] = utils.string_unicode(status_name)
			task["status_id"] = int(status_code) if status_code is not None else status_code
			task["status_xpm"] = utils.string_byte(status_xpm) if status_xpm is not None else None
			task["status_icon"] = status_icon
			task["status_order"] = status_order
			# Start
			start = t[dbtypes.TASK_DATA_HUMAN_START]
			if start is None:
				start = t[dbtypes.TASK_DATA_OFFSET]
			task["start"] = datetime.datetime(2000, 1, 1, 3) + datetime.timedelta(start)
			# End
			end = t[dbtypes.TASK_DATA_HUMAN_FINISH]
			if end is None:
				end = start + (t[dbtypes.TASK_DATA_DURATION] if t[dbtypes.TASK_DATA_DURATION] is not None else 0)
			task["end"] = datetime.datetime(2000, 1, 1, 3) + datetime.timedelta(end)
			# Progress
			task["progress"] = t[dbtypes.TASK_DATA_PROGRESS]
			# Activity name
			task["activity"] = utils.string_unicode(t[dbtypes.TASK_DATA_ACTIVITY_NAME])
			task["activity_id"] = int(t[dbtypes.TASK_DATA_ACTIVITY_ID])
			# Has child tasks
			task["is_folder"] = cclib.has_flag(t[dbtypes.TASK_DATA_FLAGS], dbtypes.TASK_FLAG_HAS_CHILD)
			# Parent task
			task["parent"] = int(t[dbtypes.TASK_DATA_PARENT_ID])
			# Empty files
			#task["files"] = None
			# Empty task definition
			task["definition"] = ""
			task["messages"] = []
			# Config valid status
			task["valid_task"] = None
			task["valid_parent"] = None
			# Config name editable
			task["name_editable"] = False
			# Publish status name
			task["publish_status"] = None
			# Universe ID
			task["unid"] = self.unid_by_prjid[int(t[dbtypes.TASK_DATA_PROJECT_ID])]
			# Updated ts
			task["last_update"] = current_time
			# Task order from db
			task["order"] = int(t[dbtypes.TASK_DATA_ORDER])
			# Custom color indicator
			task["indicator"] = None

			self.tasks_requested.append(task["id"])
			self.alltasks[task["id"]] = task

		return True
