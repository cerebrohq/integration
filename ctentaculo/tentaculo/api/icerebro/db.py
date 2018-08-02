# -*- coding: utf-8 -*-
import os, time, datetime, base64, copy, locale

# Ensure libs3 are in sys.path
from tentaculo.core import capp
capp.include_libs3()

try:
	from pycerebro import dbtypes, database, cclib
except:
	try:
		from py_cerebro import dbtypes, database, cclib
	except:
		from py_cerebro2 import dbtypes, database, cclib


from tentaculo.core import jsonio, clogger, config, vfile
from tentaculo.gui import wapp, wlogin

from tentaculo.api.icerebro import cargo

default_address = 'db.cerebrohq.com:45432'

# common db utility class
# WARNING: This is SINGLETON
class Db(object):
	# singleton	
	__instance = None

	def __new__(cls, *args, **kwargs):
		if not isinstance(cls.__instance, cls):
			cls.__instance = super(Db, cls).__new__(cls, *args, **kwargs)
			cls.__instance()
		return cls.__instance

	def __call__(self):		
		self.log = clogger.CLogger().log
		self.config = config.Config()
		self.load_config()
		self.disconnect()

	# full clear with 'disconnect'
	def disconnect(self):	
		self.connected = False		
		self.db = None
		self.cargo = None
		self.current_parent = 0	
		self.clear_profile()	
		self.clear_data()
		
	def clear_data(self):
		self.allocated = set()
		self.tree = {}
		self.links = {}
		self.alltasks = {}		

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
				self.user_name = capp.string_unicode(u[dbtypes.USER_DATA_FULL_NAME])
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
		doc_dir = capp.homedir()
		if os.path.exists(doc_dir):
			dir = doc_dir
		else:
			dir = wapp.directory('Select woking directory')

		if dir is None or not os.path.exists(dir):
			dir = os.path.join(capp.tempdir(), capp.HOST_NAME)
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
			wapp.error(capp.string_unicode(str(err)))

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

	def login(self, relogin = False):

		if self.connected:
			return True

		self.log.info('Auto-login started...')		
		
		acc = self.account()		
		
		dbaddress = acc.get('address').split(':')
		try:			
			self.db = database.Database(dbaddress[0], dbaddress[1])
			self.log.info('Connection address: %s', dbaddress)
			MAKE_REMOVE_connect_from_cerebro_client = None
			err = self.db.connect_from_cerebro_client()
			if err == 0:
				user_id = self.db.current_user_id()
				if acc.get('id') and acc.get('id') != user_id:
					err = 1
				else:
					acc['id'] = user_id
					
			if err != 0:
				if (relogin or self.cfg.get('autologin') == True) and acc.get('psw'):
					self.db.connect(acc.get('login'), acc.get('psw'))
				else:
					acc = self.login_to(acc)
					if not acc:
						return False

		except Exception as err:
			self.log.debug('EXCEPTION', exc_info=1)
			wapp.error('Connection to {0} on port {1} failed.\n Please check address, your login and password.'.format(dbaddress[0], dbaddress[1]))
			acc = self.login_to(acc)
			if not acc:
				return False	

		self.connected = True		
		if not self.is_current_account(acc):
			self.at_logon(acc)
		
		self.log.info('Auto-login %s has been successfully.', self.user_name)
		return True;		

	# private: login with dialog
	def login_to(self, acc):
		dlogin = wlogin.Wlogin(parent = capp.app_window())
		acc = dlogin.start_login(self.login_as, acc, self.cfg.get('autologin'), self.cfg.get('remember'), self.cfg.get('accounts'))
		if acc:
			self.cfg.update({'autologin': dlogin.autologin()})	
			self.cfg.update({'remember': dlogin.remember()})			
		
		return acc

	# private: login from dialog
	def login_as(self, acc):
		dbaddress = ''
		try:		
			if not self.is_current_account(acc):
				self.disconnect()
				address = acc.get('address')
				dbaddress = address.split(':')			
				self.db = database.Database(dbaddress[0], dbaddress[1])

			self.db.connect(acc.get('login'), acc.get('psw'))	

		except Exception as err:
			self.log.debug('EXCEPTION', exc_info=1)
			wapp.error('Connection to {0} on port {1} failed.\n Please check address, your login and password.'.format(dbaddress[0], dbaddress[1]))
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

		acc.setdefault('address', default_address)

		return acc

	def is_current_account(self, acc):
		return acc and self.current_acc and self.current_acc.get('address', '') == acc.get('address') and self.current_acc.get('id', '') == acc.get('id')

	def load_config(self):
		self.log.debug('Loading connection config started...')
		
		self.cfg = jsonio.read(os.path.join(capp.configdir(), '.ula'))
		self.cfg.setdefault('autologin', True)	
		self.cfg.setdefault('remember', True)
		self.cfg.setdefault('lastlogin', None)
		self.cfg.setdefault('accounts', [])

		accs = self.cfg.get('accounts')
		
		for acc in accs:
			if acc.get('psw'):
				try:
					acc["psw"] = capp.string_unicode(base64.b64decode(capp.string_byte(acc["psw"]))[:-len(acc["login"])])
				except Exception:
					acc["psw"] = u''
		

		self.log.debug('Autologin: %s, Remember: %s, Lastlogin: %s', self.cfg.get('autologin'), self.cfg.get('remember'), self.cfg.get('lastlogin')) 
		MAKE_REMOVE = None
		#self.log.debug('REMOVE %s', self.cfg) 
		self.log.debug('Loading connection config has been successfully.')

	def save_config(self):		
		self.log.debug('Save connection config started...')

		#self.log.debug('current acc %s', self.current_acc)
		#self.log.debug('user_id %s', self.user_id)
		
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
				acc["psw"] = capp.string_unicode(base64.b64encode(capp.string_byte(acc["psw"] + acc["login"])))

			jsonio.write(os.path.join(capp.configdir(), '.ula'), save_cfg)

		self.log.debug('Save connection config has been successfully.')

	# private: query executed
	def execute(self, func, args):
		res = None
		try:
			try:
				res = func(*args)
			except Exception as err:
				self.log.debug('EXCEPTION', exc_info=1)
				if self.login(relogin = True):
					res = func(*args)
		except Exception as err:
			self.log.debug('EXCEPTION', exc_info=1)
			wapp.error(capp.string_unicode(str(err)))

		return res

	def current_user(self):
		return (self.user_id, self.user_name)

	def set_parent(self, task_id = None):
		if task_id is None:
			task_id = self.task(self.current_parent)["parent"]
						
		task =  self.task(task_id)
		
		if task_id == 0 or (task is not None and task["is_folder"]):
			self.current_parent = task_id			
			return True

		return False	

	def tasks(self):
		return self.children_tasks(self.current_parent)

	def children_tasks(self, parent_id):
		task_list = None
		if self.tree.get(parent_id, None) is None:
			self.execute(self.z_tasks, (parent_id,))

		children = self.tree.get(parent_id, None)
		if children is not None:
			task_list = { task_id: self.alltasks[task_id] for task_id in children }

		return task_list

	def linked_tasks(self, task_id):
		task_list = None
		if self.links.get(task_id, None) is None:
			self.execute(self.z_linked, (task_id,))

		linked = self.links.get(task_id, None)
		if linked is not None:
			task_list = { task_id: self.alltasks[task_id] for task_id in linked }

		return task_list

	def allocated_tasks(self, showComplete = False):	
		if len(self.allocated) == 0:
			self.execute(self.z_allocated_tasks, (showComplete,))

		todo = { task_id : self.alltasks[task_id] for task_id in self.allocated }

		return todo

	def task_files(self, task_id = None):
		if task_id is None: return None

		task = self.task(task_id)
		if task is not None:
			files = task.get("files", None)
			if files is None:
				self.execute(self.z_task_files, (task_id,))

		return task.get("files", {})

	def task_statuses(self, task_id):
		return self.execute(self.z_task_statuses, (task_id,))

	def set_work_status(self, task_id):
		return self.execute(self.z_set_work_status, (task_id,))

	def send_report(self, taskid, text, status, ver_file, ver_thumb, work_time = 0, links = [], attachments = []):
		return self.execute(self.z_send_report, (taskid, text, status, ver_file, ver_thumb, work_time, links, attachments))

	def refresh(self):	
		self.clear_data()
		self.allocated_tasks()
		self.tasks()

	def refresh_task(self, task_id):
		if task_id is None: return None

		self.alltasks.pop(task_id, None)

		return self.task(task_id)
		
	def task(self, task_id = None):
		if task_id is None: return None
		
		tsk = self.alltasks.get(task_id, None)
		if tsk is None:
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
					path = task["path_repr"] + " > " + task["name"]
		if len(path) > 50:
			path = u"..." + path[-50:]
		return path
	
	# private: 
	def z_tasks(self, parent_id):
		if self.tree.get(parent_id, None) is None:
			tsks = []
			if parent_id == 0:
				tsks = self.db.root_tasks()
			else:
				tsks = self.db.task_children(parent_id)

			self.tree[parent_id] = { tsk[dbtypes.TASK_DATA_ID] for tsk in tsks if tsk is not None }
			self.update_tasks(tsks)

	def z_linked(self, task_id):
		if self.links.get(task_id, None) is None:
			links = self.db.task_links(task_id)

			self.links[task_id] = { l[dbtypes.TASK_LINK_SRC] for l in links if l[dbtypes.TASK_LINK_DST] == task_id }
			tsks = self.db.tasks(self.links[task_id])
			self.update_tasks(tsks)
			
	# private: 
	def z_task(self, task_id):
			task = self.db.task(task_id)			
			self.update_tasks([task,])

	# private: 
	def z_allocated_tasks(self, showComplete = False):	
			   
		db_tasks = self.db.to_do_task_list(self.user_id, showComplete)
		# Complete statuses
		statuses_set = set([st[dbtypes.STATUS_DATA_ID] for st in self.statuses if cclib.has_flag(st[dbtypes.STATUS_DATA_FLAGS], dbtypes.STATUS_FLAG_WORK_STOPPED)])

		tasks = [task for task in db_tasks if showComplete or task[dbtypes.TASK_DATA_CC_STATUS] not in statuses_set]

		self.allocated = { task[dbtypes.TASK_DATA_ID] for task in tasks if task is not None }

		self.update_tasks(tasks)	

	def z_task_statuses(self, task_id):
		rstatuses = []
		if not task_id is None:
			pstatuses = self.db.task_possible_statuses(task_id)
			pstatuses.sort(key=lambda val: val[dbtypes.STATUS_DATA_ORDER])
			rstatuses = [[capp.string_unicode(st[dbtypes.STATUS_DATA_NAME]), int(st[dbtypes.STATUS_DATA_ID]), st[dbtypes.STATUS_DATA_FLAGS]] for st in pstatuses if st[dbtypes.STATUS_DATA_NAME] is not None]
		return rstatuses

	# private: 
	def z_task_files(self, task_id = None):

		if task_id is None: return None
		files = {}
		self.alltasks[task_id]["definition"] = ""
		self.alltasks[task_id]["messages"] = []

		task_msgs = self.db.task_messages(task_id)

		# Append local and publish files
		conf = self.config.translate(self.alltasks[task_id])
		fvers = vfile.VFile(conf)
		last_version = None if not fvers.has_versions else fvers.versions[fvers.last_number]
		publish, local = fvers.publish_path(), fvers.local_path()
		if publish is not None and os.path.exists(publish) and os.path.splitext(publish)[1] in capp.HOST_EXT:
			file = {}
			file["name"] = os.path.basename(publish)
			file["path"] = os.path.normpath(publish)
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
			file["path"] = os.path.normpath(local)
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
				self.alltasks[task_id]["uname"] = capp.string_unicode(m[dbtypes.MESSAGE_DATA_CREATOR_NAME])

			# check definition
			if m[dbtypes.MESSAGE_DATA_TYPE] == dbtypes.MESSAGE_TYPE_DEFINITION:
				msg = m[dbtypes.MESSAGE_DATA_TEXT]
				if msg is not None:
					self.alltasks[task_id]["definition"] += capp.string_unicode(msg)
					self.alltasks[task_id]["definition"] += '\n'

			if m[dbtypes.MESSAGE_DATA_TYPE] != dbtypes.MESSAGE_TYPE_DEFINITION:
				msg = m[dbtypes.MESSAGE_DATA_TEXT]
				if msg is not None:
					text = date.strftime("%d.%m.%Y")
					if not capp.PY3: text = text.decode(locale.getpreferredencoding())
					self.alltasks[task_id]["messages"].append({'author' : capp.string_unicode(author), 'date' : text, 'msg' : capp.string_unicode(msg) })

		dbfiles = self.db.message_attachments(set(msgids))
		link_files = { f[dbtypes.ATTACHMENT_DATA_GROUP_ID] :
			  {"id" : int(f[dbtypes.ATTACHMENT_DATA_ID]), "path" : capp.string_unicode(f[dbtypes.ATTACHMENT_DATA_FILE_NAME]), "thumbs" : [], "date" : f[dbtypes.ATTACHMENT_DATA_CREATED] }
			  for f in dbfiles if f[dbtypes.ATTACHMENT_DATA_TAG] == dbtypes.ATTACHMENT_TAG_LINK
			}

		for f in dbfiles:
			if f[dbtypes.ATTACHMENT_DATA_GROUP_ID] in link_files and f[dbtypes.ATTACHMENT_DATA_TAG] == dbtypes.ATTACHMENT_TAG_THUMB1:
				link_files[f[dbtypes.ATTACHMENT_DATA_GROUP_ID]]["thumbs"].append(f[dbtypes.ATTACHMENT_DATA_HASH])

		for f in link_files.values():
			file_thumb = None
			for hash_db in reversed(f["thumbs"]):
				file_thumb = self.cargo.file(hash_db)
				if file_thumb is not None:
					break

			path = f["path"]
			if os.path.splitext(path)[1] in capp.HOST_EXT:
				path = self.config.redirect_path(path)
				filename = os.path.basename(path)
				file = {}
				file["name"] = filename
				file["path"] = path
				file["thumbnail"] = file_thumb
				file["id"] = f["id"]
				file["version"] = fvers.file_version(path)
				file["is_last_version"] = False if last_version is None else last_version == filename
				file["date"] = f["date"]
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
				self.log.error(str(err))

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
	def z_set_work_status(self, task_id):
		
		task = self.task(task_id)
		if task:
			status = None
			statuses = self.task_statuses(task_id)
			for st in statuses:
				if cclib.has_flag(st[2], dbtypes.STATUS_FLAG_WORK_STARTED):
					if st[1] != task["status_id"]:
						status = st[1]
					break
			
			if status is not None:
				self.db.task_set_status(task_id, status)
				self.allocated = set()
				self.allocated_tasks()
				return True

		return False

	# private: to update tasks data
	def update_tasks(self, tasks_db = None):
		if tasks_db is None: return False

		for t in tasks_db:
			if t is None: continue
			task = {}
			# ID
			task["id"] = int(t[dbtypes.TASK_DATA_ID])
			# Thumb
			thumb = None

			if t[dbtypes.TASK_DATA_THUMBS] is not None:
				tmp = t[dbtypes.TASK_DATA_THUMBS].split(',')
				hashes = [tmp[x] if len(tmp) > x and len(tmp[x]) > 0 else None for x in range(6)]
				hashes = hashes[0:2] + hashes[3:5]

				for h in reversed(hashes):
					thumb = self.cargo.file(h)						
					if thumb is not None:
						break

			task["thumbnail"] = thumb
			# Name
			task["name"] = capp.string_unicode(t[dbtypes.TASK_DATA_NAME])
			# Path
			task["path"] = capp.string_unicode(t[dbtypes.TASK_DATA_PARENT_URL])
			task["path_repr"] = task["path"][1:-1].replace("/", " > ")
			# UserID that has task in progress
			task["owned_user_id"] = None
			task["uname"] = None
			task["enabled_task"] = True
			# Status
			status_code = t[dbtypes.TASK_DATA_SELF_STATUS]
			status_name = ""
			status_icon = None
			status_order = 0
			for st in self.statuses:
				if status_code == st[dbtypes.STATUS_DATA_ID]:
					if cclib.has_flag(st[dbtypes.STATUS_DATA_FLAGS], dbtypes.STATUS_FLAG_WORK_STARTED):
						task["owned_user_id"] = 0
						task["enabled_task"] = False
					status_name = st[dbtypes.STATUS_DATA_NAME]
					status_icon = st[dbtypes.STATUS_DATA_ICON]
					status_order = int(st[dbtypes.STATUS_DATA_ORDER])
					break
			if status_name is None: status_name = ""
			task["status"] = capp.string_unicode(status_name)
			task["status_id"] = status_code
			task["status_icon"] = capp.string_byte(status_icon) if status_icon is not None else None
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
			task["activity"] = capp.string_unicode(t[dbtypes.TASK_DATA_ACTIVITY_NAME])
			task["activity_id"] = int(t[dbtypes.TASK_DATA_ACTIVITY_ID])
			# Has child tasks
			task["is_folder"] = cclib.has_flag(t[dbtypes.TASK_DATA_FLAGS], dbtypes.TASK_FLAG_HAS_CHILD)
			# Parent task
			task["parent"] = int(t[dbtypes.TASK_DATA_PARENT_ID])
			# Empty files
			task["files"] = None
			# Empty task definition
			task["definition"] = ""
			task["messages"] = []
			# Config valid status
			task["valid_task"] = None
			task["valid_parent"] = None
			# Config name editable
			task["name_editable"] = False
			task["name_list"] = []
			# Universe ID
			task["unid"] = int(self.db.execute('select * from "getUnid_byPrj"(%s)', int(t[dbtypes.TASK_DATA_PROJECT_ID]))[0][0])
			if task["unid"] not in self.config.config_pool:
				cfg = jsonio.parse(self.db.execute('select * from "attributeUniverse"(%s, 120)', task["unid"])[0][0])
				self.config.set_config(task["unid"], cfg)

			self.alltasks[task["id"]] = task

		return True
