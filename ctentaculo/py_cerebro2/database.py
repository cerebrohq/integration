# -*- coding: utf-8 -*-

# Модуль доступа к базе данных Cerebro
"""
Используемые сторонние модули:
psycopg2 (http://initd.org/psycopg/) - используется для осущевстления доступа к базе данных PostgreSQL


Выполнение запросов к базе данных всегда сопровождается
одним дополнительным запросом на подтверждение авторизованного пользователя.
Kласс Database, описанный в этом модуле, берет на себя эту специфическую функциональность,
чтобы не приходилось каждый раз писать в коде дополнительные конструкции.
Также, клаcc Database содержит несколько полезных функций для работы с данными Cerebro

::
	#Пример установки соединения и выполнения запроса

	db = database.Database('cerebrohq.com', 45432)

	db.connect('user', 'password')

	result = db.execute('select * from _task_list_00(%s, %s)', (0, 0))
::

Класс является надстройкой над модулем psycopg2.
Вы можете использовать модуль psycopg2 и не использовать этот класс.
Но тогда вы должны перед каждым запросом
исполнять запрос на подтверждение авторизации пользователя.

::
	#Пример установки соединения и выполнения запроса напрямую через модуль psycopg2

	import psycopg2

	dbcon = psycopg2.connect(host='cerebrohq.com', port=45432, database="memoria", user="sa_web", password="web")

	dbcon.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # Выставляем автоматический комит транзакций
	db = dbcon.cursor()
	db.execute('select "webStart"(%s, %s)', (db_user, db_password)) # Выполняем запрос на авторизацию пользователя.
	rsid = db.fetchall()
	sid = int(rsid[0][0]) # В качестве результата получаем идентификатор авторизованного пользователя.

	db.execute('select "webResume2"(%s)', (sid,)) # Выполняем запрос на подтверждение авторизации пользователя

	db.execute('select * from _task_list_00(%s, %s)', (0, 0))

	result = db.fetchall()

	db.close() # закрываем соединение
	dbcon.close()
::
"""

import os
import re
import socket
import struct
import psycopg2 # модуль доступа к базе данных postgresql
import threading
from .cclib import *
from .dbtypes import *
import collections
import time
from psycopg2.extras import DictCursor

def get_val_by_type(val_id):
	if type(val_id) == set:
		return val_id
	else:
		ids = set()             
		ids.add(val_id)
		return ids

class Set_to_sql_arr:
	def __init__(self, obj_set):
		self.obj = obj_set

	def getquoted(self):
		sql_str = "'{"
		for i in self.obj:
			if sql_str != "'{":
				sql_str += ','

			sql_str += '%s' % i

		sql_str += "}'"
		#print sql_str
		return sql_str

class Database():
	"""
	Класс Database для установления соединения с базой данных и выполнения sql запросов.
	"""

	def __init__(self, db_host, db_port, db_timeout = 5,  db_reconn_count = 3):

		self.db_host = db_host
		self.db_port = db_port
		self.db_timeout = db_timeout
		self.db_reconn_count = db_reconn_count
		self.disconnected_by_timer = False
		self.is_connected_by_client = False		

		self.dbcon = None
		self.db = None
		self.sid = -1

		psycopg2.extensions.register_adapter(set, Set_to_sql_arr)
		
	def __del__(self):
		self.__disconnectDB()

	def __disconnectDB(self):
		if self.db != None and self.db.closed == False:
			self.db.close()
		
		if self.dbcon != None and self.dbcon.closed == False:		
			self.dbcon.close()

		self.disconnected_by_timer = True

	def __reconnectDB(self):
		self.__disconnectDB()
		if self.is_connected_by_client:
			err = self.connect_from_cerebro_client()
			if err != 0:
				raise Exception('Connection Error')
		else:
			self.connect(self.db_user, self.db_password)

		self.disconnectTask.cancel()

	def connect(self, db_user, db_password):
		"""
		Соединение с базой данных с авторизацией.
		"""

		self.disconnected_by_timer = False
		self.is_connected_by_client = False
		self.db_user = db_user
		self.db_password = db_password

		self.dbcon = psycopg2.connect(host=self.db_host, port=self.db_port, database="memoria", user="sa_web", password="web", cursor_factory=DictCursor)
		"""
		Обратите внимание, что для соединение с базой данных memoria происходит их под пользователя sa_web.
		Авторизация пользователя производится уже после установки соединения
		"""

		self.dbcon.set_client_encoding('UTF8')
		self.dbcon.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # Выставляем автоматический комит транзакций
		self.db = self.dbcon.cursor()
		self.db.execute('select "webStart"(%s, %s)', (db_user, db_password))
		rsid = self.db.fetchall()
		self.sid = int(rsid[0][0])
		if(self.sid==-1):
			raise Exception('Login is invalid');

		self.disconnectTask = threading.Timer(self.db_timeout, self.__disconnectDB)
		self.disconnectTask.start()

	def connect_from_cerebro_client(self):
		"""
		Соединение с базой данных с уже авторизованным пользователем в клиенте Cerebro.
		Такое соединения возможно, если на том же комьютере уже запущен клиент Cerebro, и произведен вход.
		В этом случаи произойдет соединение с базой данных из-под пользователя, вошедшего в клиент.
		При этом соединение в клиенте не прервется, в отличии от обычного соединения Database.connect по логину и паролю, 
		который прервет установленное соединение из-под того же пользователя в клиенте.
			
		Возвращает статус соединения:
		0 - соединение установлено
		1 - соединение не установлено (клиент Cerebro запущен, но не произведен вход)
		2 - соединение не установлено (клиент Cerebro не запущен)
		
		::
			# Устанавливаем соединение с базой данных
			if db.connect_from_cerebro_client() != 0: # Пробуем установить соединение с помощью запущенного клиента Cerebro. 
				# Если не выходит, устанавливаем соединение с помощью логина и пароля
				db.connect(db_user, db_password)  
		::
		"""		

		status = 2
		self.disconnected_by_timer = False		
		try:
			cerebro_port = 51051
			conn = socket.create_connection(('127.0.0.1',  cerebro_port),)

			proto_version = 3
			packet_type = 5

			msg = struct.pack('II',  proto_version,  packet_type)
			header = struct.pack('II', 0xEEEEFF01, len(msg))

			conn.send(header+msg)
			data = conn.recv(1024)

			res = struct.unpack_from('IIQ', data, 0)
			if res[0] == 0xEEEEFF01:
				session_id = res[2]
				if session_id == 0:
					status = 1
				else:
					status = 0
					self.dbcon = psycopg2.connect(host=self.db_host, port=self.db_port, database="memoria", user="sa_web", password="web", cursor_factory=DictCursor)
					self.dbcon.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # Выставляем автоматический комит транзакций
					self.db = self.dbcon.cursor()
					self.sid = session_id # устанавливаем идентификатор авторизованного пользователя.

					self.is_connected_by_client = True

					self.disconnectTask = threading.Timer(self.db_timeout, self.__disconnectDB)
					self.disconnectTask.start()					
					
			conn.close()
			
		except Exception as err:
			print(err)
			
		return status	

	def execute(self, query, *parameters):
		"""
		Принимает на вход текст и параметры запроса(кортеж).
		Выполняет запрос и возвращает результат. Результат представлен в виде таблицы(списoк кортежей)
		"""	
		
		if self.disconnected_by_timer or self.db == None or self.db.closed:
			self.__reconnectDB()
		else:	
			self.disconnectTask.cancel()

		try:
			pars = (self.sid,) + parameters
			self.db.execute('select "webResume2"(%s);' + query,  pars)
		except psycopg2.Error as err:
			if err.pgcode in {'08000', '08003', '08006', '08001', '08004', '08007', '08P01'} or \
			err.pgerror == 'server closed the connection unexpectedly\n\tThis probably means the server terminated abnormally\n\tbefore or while processing the request.\n':
				showError = True
				for x in range(0, self.db_reconn_count):
					try:
						self.__reconnectDB()						

						pars = (self.sid,) + parameters
						self.db.execute('select "webResume2"(%s);' + query,  pars)
						showError = False
						break
					except Exception as err:
						if err.pgcode not in {'08000', '08003', '08006', '08001', '08004', '08007', '08P01'} and \
						err.pgerror != 'server closed the connection unexpectedly\n\tThis probably means the server terminated abnormally\n\tbefore or while processing the request.\n':
							raise
						time.sleep(5)						
									
				if showError:
					raise Exception('Connection Error')
			else:
				raise	
		

		table = None
		try:
			table = self.db.fetchall()
		except psycopg2.Error as err:
			if 'cursor already closed' in str(err):					
				print('cursor already closed')
				self.__reconnectDB()						

				self.db.execute('select "webResume2"(%s);' + query,  pars)
				table = self.db.fetchall()					
			else:
				raise
		
		#print(table)

		self.disconnectTask = threading.Timer(self.db_timeout, self.__disconnectDB)
		self.disconnectTask.start()

		return table	

	def current_user_id(self):
		"""
		Возвращает идентификатор пользователя, из-под которого произошёл логин.
		"""

		user_id = self.execute('select get_usid()')
		if len(user_id) == 1:
			return user_id[0][0]

		return None

	def root_tasks(self):
		"""
		Возвращает таблицу корневых задач.

		Поля таблицы описаны в модуле dbtypes:  TASK_DATA_...
		"""

		tasks = self.execute('select uid from "_task_list_00"(0,0)')

		ids = set()
		for task in tasks:
			ids.add(task[0])

		return self.execute('select * from "taskQuery_11"(%s)',  ids)

	def to_do_task_list(self, user_id,  with_done_task):
		"""
		Возвращает таблицу задач на которых пользователь(пользователи) назначен исполнителем.

		Входные аргументы:
		integer, set(int, ) или list(int, ) user_id - идентификатор пользователя или список идентификаторов пользователей (материального ресурса)
		boolean with_done_task - если равен True, то возвратится список вместе с выполненными(у которых прогресс 100%) задачами, иначе без них

		Поля таблицы описаны в модуле dbtypes:  TASK_DATA_...
		"""
		tasks = self.execute('select uid from "taskAssigned_byUsers"(%s, %s)',  get_val_by_type(user_id), with_done_task)
		
		ids = set()
		for task in tasks:              
			ids.add(task[0]) 	
		
		return self.execute('select * from "taskQuery_11"(%s)',  ids)
		#dset = set()
		#dset.add(user_id)
		#tasks = self.execute('select uid from "taskAssigned_byUsers"(%s, %s)',  dset, with_done_task)

		#ids = set()
		#for task in tasks:
		#	ids.add(task[0])

		#return self.execute('select * from "taskQuery_11"(%s)',  ids)

	def task(self,  task_id):
		"""
		Возвращает данные по задаче.

		Поля таблицы описаны в модуле dbtypes:  TASK_DATA_...
		"""	
		
		dset = set()
		dset.add(task_id)
		task = self.execute('select * from "taskQuery_11"(%s)', dset)
		if len(task) == 1:
			return task[0]

		return None

	def tasks(self,  task_ids):
		"""
		Возвращает данные по задачам.

		Поля таблицы описаны в модуле dbtypes:  TASK_DATA_...
		"""	
		
		tasks = self.execute('select * from "taskQuery_11"(%s)', task_ids)
		if len(tasks) > 0:
			return tasks
			
		return None

	def copy_tasks(self, task_id, tasks_list, \
				flags = COPY_TASKS_SUB_TASKS|COPY_TASKS_INTERNAL_LINKS|COPY_TASKS_TAGS|COPY_TASKS_ASSIGNED_USERS|COPY_TASKS_EVENTS):
		"""
		Копирует задачи.

		Входные аргументы:
		task_id	- идентификатор задачи в которую вставляются скопированные задачи
		tasks_list - список кортежей типа [(id1, name1), (id2, name2),]
		flags - флаги копирования. Подробное описание в модуле dbtypes: COPY_TASKS_...

		Если одну задачу нужно скопировать несколько раз (реплицировать), то необходимо передать в tasks_list
	    список кортежей	с одинаковыми идентификаторами и разными именами. Например:

		[(123, 'test_task02'), (123, 'test_task03'), (123, 'test_task04'), (123, 'test_task05')]

		123 - идентификатор задачи, которую нужно скопировать
		'test_task02', 'test_task03', ... - имена новых задач.
		"""

		tids = []
		names = []

		for task_list_id, task_list_name in tasks_list:
			tids.append(task_list_id)
			names.append(task_list_name)
		tasks = self.execute('select "dupVTask"(%s,%s,%s,%s)',  tids, names, task_id, flags)
		
		ids = set()
		for task in tasks:              
			ids.add(task[0])

		return ids

	def task_children(self,  task_id):
		"""
		Возвращает таблицу подзадач.

		Поля таблицы описаны в модуле dbtypes:  TASK_DATA_...
		"""
		tasks = self.execute('select uid from "_task_list_00"(%s,0)',  task_id)

		ids = set()
		for task in tasks:
			ids.add(task[0])

		return self.execute('select * from "taskQuery_11"(%s)',  ids)


	def task_allocated(self,  task_id):
		"""
		Возвращает таблицу аллоцированных пользователей (исполнителей) на задачу.

		Поля таблицы описаны в модуле dbtypes:  TASK_ALLOCATED_...
		"""
		return self.execute('select uid, "userNameDisplay"(uid) as name, "userGetFlags"(uid) as flags from "assignedUsersTask"(%s) as uid order by name',  task_id)

	def task_attachments(self,  task_id):
		"""
		Возвращает таблицу вложений задачи(задач).

		Поля таблицы описаны описаны в модуле dbtypes:  ATTACHMENT_DATA_...

		Одно вложение может представлять собой от 1-й до 5-ти записей в таблице.
		Объеденениы записи вложения идентификатором группы - dbtypes.ATTACHMENT_DATA_GROUP_ID.
		Записи одного вложения отличаются тегом - dbtypes.ATTACHMENT_DATA_TAG, и означают то или иное свойство вложения.

		Вложение бывает двух видов: файл и линк на файл. В первом случаи у вложения присутствует запись
		с тегом dbtypes.ATTACHMENT_TAG_FILE, которая содержит хеш файла лежащего в файловом хранилище Cargador.
		В случаи если файл приложен к соообщению как линк, то присутствует запись с тегом dbtypes.ATTACHMENT_TAG_LINK.
		Эта запись не имеет хеша и в поле имени dbtypes.ATTACHMENT_DATA_FILE_NAME у неё прописан полный путь до файла.
		Запись с тегом рецензии, dbtypes.ATTACHMENT_TAG_REVIEW, присутствует только если к файлу добавлена рицензия
		из инструмента рецензирования Mirada.
		Записи с тегом эскизов dbtypes.ATTACHMENT_TAG_THUMB..., присутствуют только если файл является изображением или видео.
		В случаи изображения присутствует только одна запись dbtypes.ATTACHMENT_TAG_THUMB1, если изображение - три записи.

		"""

		return self.execute('select * from "listAttachmentsTasks"(%s, false)',  get_val_by_type(task_id))

	def task_links(self,  task_id):
		"""
		Возвращает таблицу связей задачи.

		Поля таблицы описаны в модуле dbtypes:  TASK_LINK_...
		"""
		return self.execute('select * from "ggLinks_byTask"(%s)',  task_id)

	def task_definition(self,  task_id):
		"""
		Возвращает данные сообщения типа постановка задачи.

		Поля таблицы описаны в модуле dbtypes:  MESSAGE_DATA_...
		"""	
		
		id = self.execute('select "getTaskDefinitionId"(%s)',  task_id)
		if (len(id) == 1  and id[0][0] != None):
			dset = set()
			dset.add(id[0][0])
			definition = self.execute('select * from "eventQuery_08"(%s)',  dset)
			if len(definition) == 1:
				return definition[0]

		return None

	def task_messages(self,  task_id):
		"""
		Возвращает таблицу сообщений задачи.

		Поля таблицы описаны в модуле dbtypes:  MESSAGE_DATA_...
		Типы сообщений описаны в модуле dbtypes:  MESSAGE_TYPE_...
		"""

		messs = self.execute('select uid from "_event_list"(%s, false)',  task_id)
		ids = set()
		for mess in messs:
			ids.add(mess[0])

		return self.execute('select * from "eventQuery_08"(%s)',  ids)

	def task_possible_statuses(self,  task_id):
		"""
		:param int task_id: task ID.
		:returns: the table of statuses, which can be set for the task.

		The table fields are described in the module dbtypes: :py:const:`STATUS_DATA_...<py_cerebro.dbtypes.STATUS_DATA_>`
		
		In the Cerebro system for each status, permissions for switching each status are set.
		In addition, each status has a flag of inheritance.
		On the task-containers you can set only the statuses that have this flag enabled.
		Therefore, the list of possible statuses depends on user rights, the current status,
		as well as the presence / lack of sub-tasks in the task.
		"""  
		return self.execute('select * from "statusListByTask"(%s)',  task_id)

	def message(self,  message_id):
		"""
		Возвращает данные сообщения.

		Поля таблицы описаны в модуле dbtypes:  MESSAGE_DATA_...
		Типы сообщений описаны в модуле dbtypes:  MESSAGE_TYPE_...
		"""

		dset = set()
		dset.add(message_id)
		mess = self.execute('select * from "eventQuery_08"(%s)',  dset)
		if len(mess) == 1:
			return mess[0]

		return None

	def messages(self,  message_ids):
		"""
		Возвращает данные сообщений.

		Поля таблицы описаны в модуле dbtypes:  MESSAGE_DATA_...
		Типы сообщений описаны в модуле dbtypes:  MESSAGE_TYPE_...
		"""
		
		mess = self.execute('select * from "eventQuery_08"(%s)',  message_ids)	
		if len(mess) > 0:
			return mess	
		
		return None

	def message_attachments(self,  message_id):
		"""
		Возвращает таблицу вложений сообщения(ий).

		Поля таблицы описаны описаны в модуле dbtypes:  ATTACHMENT_DATA_...

		Одно вложение может представлять собой от 1-й до 5-ти записей в таблице.
		Объеденениы записи вложения идентификатором группы - dbtypes.ATTACHMENT_DATA_GROUP_ID.
		Записи одного вложения отличаются тегом - dbtypes.ATTACHMENT_DATA_TAG, и означают то или иное свойство вложения.

		Вложение бывает двух видов: файл и линк на файл. В первом случаи у вложения присутствует запись
		с тегом dbtypes.ATTACHMENT_TAG_FILE, которая содержит хеш файла лежащего в файловом хранилище Cargador.
		В случаи если файл приложен к соообщению как линк, то присутствует запись с тегом dbtypes.ATTACHMENT_TAG_LINK.
		Эта запись не имеет хеша и в поле имени dbtypes.ATTACHMENT_DATA_FILE_NAME у неё прописан полный путь до файла.
		Запись с тегом рецензии, dbtypes.ATTACHMENT_TAG_REVIEW, присутствует только если к файлу добавлена рицензия
		из инструмента рецензирования Mirada.
		Записи с тегом эскизов dbtypes.ATTACHMENT_TAG_THUMB..., присутствуют только если файл является изображением или видео.
		В случаи изображения присутствует только одна запись dbtypes.ATTACHMENT_TAG_THUMB1, если изображение - три записи.

		"""

		return self.execute('select * from "listAttachmentsArray"(%s, false)',  get_val_by_type(message_id))

	def users(self):
		"""
		Возвращает таблицу пользователей/материальных ресурсов.

		Поля таблицы описаны в модуле dbtypes:  USER_DATA_...

		У материального ресурса выставлен флаг dbtypes.USER_FLAG_IS_RESOURCE
		Проверить этот флаг можно с помощью функции cclib.has_flag
		::
			if cclib.has_flag(user[dbtypes.USER_DATA_FLAGS], dbtypes.USER_FLAG_IS_RESOURCE): #если материальный ресурс
				# делать то-то
		::
		"""

		return self.execute('select uid, "userNameDisplay"(uid) as name, "userGetFlags"(uid) as flags' +
									', "userGetLogin"(uid) as lid, "userGetFirstName"(uid) as firstname, "userGetLastName"(uid) as lastname' +
									', "userGetEmail"(uid) as email, "userGetPhone"(uid) as phone, "userGetIcq"(uid) as icq from "userList"() order by name')

	def activities(self):
		"""
		Возвращает таблицу видов деятельности.

		Поля таблицы описаны в модуле dbtypes:  ACTIVITY_DATA_...
		"""
		return self.execute('select uid, name from "listActivities"(false)')

	def statuses(self):
		"""
		:returns: the table of all statuses.

		The table fields are described in the module dbtypes: :py:const:`STATUS_DATA_...<py_cerebro.dbtypes.STATUS_DATA_>`		
		"""
		return self.execute('select * from "statusList"()')

	def add_task(self,  parent_id,  name,  activity_id = 0):
		"""
		Создание новой задачи.
		Предупреждение: задача не может содержать в имени следующие символы \ / # : ? & ' " , + |

		Возвращает идентификатор новой задачи.
		
		.. note:: Для отправки уведомления пользователю о новой задаче требуется создать в задаче сообщение
			типа :py:meth:`"Постановка задачи" <py_cerebro.database.Database.add_definition>`.
		"""
		
		match = re.search(r"[\\\\/#:?&'\",|+]+", name)
		if match:
			raise Exception("Name is incorrect. Symbols \\ / # : ? & ' \" , + | are not allowed")
			
		return self.execute('select "newTask_00"(%s,%s,%s,true)',  parent_id,  name,  activity_id)[0][0]

	def task_set_name(self,  task_id,  name):
		"""
		Устанавливает новое имя задаче.
		Предупреждение: задача не может содержать в имени следующие символы \ / # : ? & ' " , + |
		"""
		
		match = re.search(r"[\\\\/#:?&'\",|+]+", name)
		if match:
			raise Exception("Name is incorrect. Symbols \\ / # : ? & ' \" , + | are not allowed")
			
		return self.execute('select "taskSetName"(%s,%s)',  task_id,  name)[0][0]

	def task_set_activity(self,  task_id,  activity_id):
		"""
		Устанавливает вид деятельности задачи(задач).
		"""
		tasks = self.execute('select "taskSetActivity_a"(%s,%s)',  get_val_by_type(task_id),  activity_id)

		ids = set()
		for task in tasks:              
			ids.add(task[0])

		return ids

	def task_set_status(self,  task_id,  status_id):
		"""
		:param task_id: task ID(s).
		:type task_id: int, set(int, ) or list(int, )
		:param int status_id: status ID.

		Sets a status for a task. Status ID = None sets the task status to 'No Status'.
		"""
		
		tasks = self.execute('select "taskSetStatus_a"(%s,%s)',  get_val_by_type(task_id),  status_id)

		ids = set()
		for task in tasks:              
			ids.add(task[0])

		return ids

	def task_set_priority(self,  task_id,  prior):
		"""
		Устанавливает приоритет задачи(задач).

		Значения приоритета описаны в модуле dbtypes:  TASK_PRIORITY_...
		"""
		tasks = self.execute('select "taskSetPriority_a"(%s,%s::smallint)',  get_val_by_type(task_id),  prior)

		ids = set()
		for task in tasks:              
			ids.add(task[0])

		return ids

	def task_set_flag(self,  task_id,  flag,  is_set):
		"""
		Устанавливает флаг у задачи(задач).
		Если аргумент is_set равен True флаг устанавливается, иначе сбрасывается

		::
			# Установка задачи в статус Закрыта
			db.task_set_flag(task_id, dbtypes.TASK_FLAG_CLOSED, True)
		::
		"""
		newFlag = 0
		if is_set:
			newFlag = 1 << flag
			
		mask	= 1 << flag
			
		self.execute('select "taskSetFlagsMulti"(%s,%s,%s)',  get_val_by_type(task_id),  newFlag,  mask)

	def task_set_progress(self,  task_id,  progress):
		"""
		Устанавливает прогресс задачи(задач).
		При установке прогреса в 100, задача считается Выполненой(Done)
		При установке прогреса в None, собственный прогресс задачи сбрасывается и расчитывается из подзадач
		"""
		tasks = self.execute('select "taskSetProgress_a"(%s,%s::smallint)',  get_val_by_type(task_id),  progress)

		ids = set()
		for task in tasks:              
			ids.add(task[0])

		return ids

	def task_set_planned_time(self,  task_id,  hours):
		"""
		Устанавливает запланированное время задачи(задач) в часах.

		Входной аргумент:
		float hours	- запланированные на задачу часы

		При установке аргумента hours в None, запланированное время задачи сбрасывается.
		После сброса запланированное время расчитывается исходя из календарных сроков задачи и расписания.
		"""
		tasks = self.execute('select "taskSetPlanned_a"(%s,%s)',  get_val_by_type(task_id),  hours)

		ids = set()
		for task in tasks:              
			ids.add(task[0])

		return ids

	def task_set_start(self,  task_id,  time):
		"""
		Устанавливает время начала задачи(задач) в днях от 01.01.2000 в UTC

		Входной аргумент:
		float time - время в днях от 01.01.2000

		Аргумент time = None сбрасывает установленное время начала задачи.
		После сброса время начала расчитывается исходя из связей задачи и расписания.

		::
			db.task_set_start({task_id, task_id1}, 4506.375) # время старта 03.05.2012 9:00 UTC
		::
		
		Пример установки времени начала задачи в текущее
		::
			import datetime

			datetime_now = datetime.datetime.utcnow()
			datetime_2000 = datetime.datetime(2000, 1, 1)
			timedelta = datetime_now - datetime_2000
			days = timedelta.total_seconds()/(24*60*60)	
	
			db.task_set_start({task_id, task_id1}, days) 
		::
		"""
		tasks = self.execute('select "ggSetTaskOffset_a"(%s,%s::double precision)',  get_val_by_type(task_id),  time)

		ids = set()
		for task in tasks:              
			ids.add(task[0])

		return ids

	def task_set_finish(self,  task_id,  time):
		"""
		Устанавливает время окончания задачи(задач) в днях от 01.01.2000 в UTC

		Входной аргумент:
		float time - время в днях от 01.01.2000

		Аргумент time = None сбрасывает установленное время окончания задачи.
		После сброса время окончания расчитывается исходя из запланированного времени на задачу и расписания

		::
			db.task_set_finish(task_id, 4506.75) # время окончания 03.05.2012 18:00 UTC
		::
		
		Пример установки времени окончания задачи через 3 дня от текущего
		::
			import datetime

			datetime_now = datetime.datetime.utcnow()
			datetime_2000 = datetime.datetime(2000, 1, 1)
			timedelta = datetime_now - datetime_2000
			days = timedelta.total_seconds()/(24*60*60) + 3	
		
			db.task_set_start(task_id, days) 
		::		
		"""
		tasks = self.execute('select "ggSetTaskStop_a"(%s,%s::double precision)', get_val_by_type(task_id),  time)

		ids = set()
		for task in tasks:              
			ids.add(task[0])

		return ids


	def task_set_budget(self,  task_id,  budget):
		"""
		Устанавливает бюджет.

		Входной аргумент:
		float budget - в условных единицах

		При установке бюджета в None, собственный бюджет задачи сбрасывается и расчитывается из подзадач
		"""
		tasks = self.execute('select "taskSetCosts_a"(%s,%s)',  get_val_by_type(task_id),  budget)

		ids = set()
		for task in tasks:              
			ids.add(task[0])

		return ids

	def task_set_allocated(self,  task_id,  user_id):
		"""
		Назначает исполнителя(исполнителей) на задачу(задачи).

		Входной аргумент:
		user_id - идентификатор пользователя(пользователей)/материального ресурса(ресурсов).
		
		.. note:: Для отправки уведомления пользователю о новой задаче требуется наличие в задаче сообщения
			типа :py:meth:`"Постановка задачи" <py_cerebro.database.Database.task_definition>`.
		"""
		tasks = self.execute('select "userAssignmentTask_a"(%s,%s,%s)',  get_val_by_type(task_id),  get_val_by_type(user_id),  1)

		ids = set()
		for task in tasks:              
			ids.add(task[0])

		return ids

	def task_remove_allocated(self,  task_id,  user_id):
		"""
		Убирает исполнителя(исполнителей) с задачи(задач).

		Входной аргумент:
		user_id - идентификатор пользователя/материального ресурса
		"""
		tasks = self.execute('select "userAssignmentTask_a"(%s,%s,%s)',  get_val_by_type(task_id),  get_val_by_type(user_id),  0)

		ids = set()
		for task in tasks:
			ids.add(task[0])

		return ids

	def task_set_hashtags(self, task_id, hashtags):
		"""
		Устанавливает хэштеги на задачи.

		Входной аргумент:
		hashtags - список хэштегов(каждый хэштег должен быть одним словом без пробелов)
		"""
		tasks = self.execute('select "htSetTask"(%s,%s,%s)', get_val_by_type(task_id), hashtags, True)

		ids = set()
		for task in tasks:
			ids.add(task[0])

		return ids

	def task_hashtags(self, task_id):
		"""
		Получает хэштеги задачи.

		"""
		hashtags = '' #self.execute('select "htSetTask"(%s,%s,%s)', get_val_by_type(task_id), hashtags, True)

		return hashtags

	def task_remove_hashtags(self, task_id, hashtags):
		"""
		Удаляет хэштеги из задач.

		Входной аргумент:
		hashtags - список хэштегов(каждый хэштег должен быть одним словом без пробелов).
		"""
		tasks = self.execute('select "htSetTask"(%s,%s,%s)', get_val_by_type(task_id), hashtags, False)

		ids = set()
		for task in tasks:
			ids.add(task[0])

		return ids

	def message_set_hashtags(self, message_id, hashtags):
		"""
		Устанавливает хэштеги на сообщения.

		Входной аргумент:
		hashtags - список хэштегов(каждый хэштег должен быть одним словом без пробелов).
		"""
		tasks = self.execute('select "htSetEvent"(%s,%s,%s)', get_val_by_type(message_id), hashtags, True)

		ids = set()
		for task in tasks:
			ids.add(task[0])

		return ids

	def message_hashtags(self, message_id):
		"""
		Получает хэштеги сообщения.

		"""
		hashtags = ''#self.execute('select "htSetEvent"(%s,%s,%s)', get_val_by_type(message_id), hashtags, True)

		return hashtags

	def message_remove_hashtags(self, message_id, hashtags):
		"""
		Удаляет хэштеги из сообщений.

		Входной аргумент:
		hashtags - список хэштегов(каждый хэштег должен быть одним словом без пробелов).
		"""
		tasks = self.execute('select "htSetEvent"(%s,%s,%s)', get_val_by_type(message_id), hashtags, False)

		ids = set()
		for task in tasks:
			ids.add(task[0])

		return ids

	def attachment_set_hashtags(self, attachment_id, hashtags):
		"""
		Устанавливает хэштеги на вложения.

		Входной аргумент:
		hashtags - список хэштегов(каждый хэштег должен быть одним словом без пробелов).

		Рекомендуется для вложений со значением тега ATTACHMENT_DATA_TAG: ATTACHMENT_TAG_FILE или ATTACHMENT_TAG_LINK.
		"""
		tasks = self.execute('select "htSetAttachment"(%s,%s,%s)', get_val_by_type(attachment_id), hashtags, True)

		ids = set()
		for task in tasks:
			ids.add(task[0])

		return ids

	def attachment_hashtags(self, attachment_id):
		"""
		Получает хэштеги вложения.

		Рекомендуется для вложений со значением тега ATTACHMENT_DATA_TAG: ATTACHMENT_TAG_FILE или ATTACHMENT_TAG_LINK.
		"""
		hashtags = ''#self.execute('select "htSetAttachment"(%s,%s,%s)', get_val_by_type(attachment_id), hashtags, True)

		return hashtags

	def attachment_remove_hashtags(self, attachment_id, hashtags):
		"""
		Удаляет хэштеги их вложений.

		Входной аргумент:
		hashtags - список хэштегов(каждый хэштег должен быть одним словом без пробелов).

		Рекомендуется для вложений со значением тега ATTACHMENT_DATA_TAG: ATTACHMENT_TAG_FILE или ATTACHMENT_TAG_LINK.
		"""
		tasks = self.execute('select "htSetAttachment"(%s,%s,%s)', get_val_by_type(attachment_id), hashtags, False)

		ids = set()
		for task in tasks:
			ids.add(task[0])

		return ids

	def set_link_tasks(self,  first_task_id,  second_task_id):
		"""
		Создает связь между двумя задачами.

		Входные аргументы:
		first_task_id - идентификатор задачи от которой идет связь
		second_task_id - идентификатор задачи к которой идет связь

		Возвращает идентификатор связи.
		"""
		dset = set()
		dset.add(first_task_id)
		dset2 = set()
		dset2.add(second_task_id)
		return self.execute('select "ggLinkAdd_a"(%s,%s,%s)',  dset,  dset2,  0)[0][0]

	def drop_link_tasks(self,  link_id):
		"""
		Удаляет связь между двумя задачами.

		Входной аргумент:
		link_id - идентификатор связи
		"""
		dset = set()
		dset.add(link_id)
		self.execute('select "ggLinkDel_a"(%s,%s)',  dset,  True)

	def add_definition(self,  task_id,  html_text):
		"""
		Добавляет сообщение типа постановка задачи.

		Входной аргумент:
		html_text - текст сообщения в формате html.

		Возвращает идентификатор нового сообщения.
		"""
		return self.execute('select "eventNew"(%s,%s,%s,%s,%s,%s)',  None,  task_id,  html_text, MESSAGE_TYPE_DEFINITION,  None,  None)[0][0]

	def add_review(self,  task_id,  message_id,  html_text,  minutes = None):
		"""
		Добавляет сообщение типа рецензия.

		Входнойые аргументы:
		message_id - идентификатор сообщения на которое пишется ответ
		html_text - текст сообщения в формате html.
		minutes - принятое время в минутах.

		Возвращает идентификатор нового сообщения.
		"""
		return self.execute('select "eventNew"(%s,%s,%s,%s,%s,%s)',  None,  task_id,  html_text, MESSAGE_TYPE_REVIEW,  message_id,  minutes)[0][0]


	def add_client_review(self,  task_id,  message_id,  html_text):
		"""
		Добавляет сообщение типа рецензия клиента.

		Входнойые аргументы:
		message_id - идентификатор сообщения на которое пишется ответ
		html_text - текст сообщения в формате html.

		Возвращает идентификатор нового сообщения.
		"""
		return self.execute('select "eventNew"(%s,%s,%s,%s,%s,%s)',  None,  task_id,  html_text, MESSAGE_TYPE_CLIENT_REVIEW,  message_id,  None)[0][0]


	def add_report(self,  task_id,  message_id,  html_text,  minutes):
		"""
		Добавляет сообщение типа отчет.

		Входнойые аргументы:
		message_id - идентификатор сообщения на которое пишется ответ
		html_text - текст сообщения в формате html.
		minutes - заявленое время отчета в минутах.

		Очень важнп устанавливать время в отчетах.
		Если minutes имеет занчение 0 или None, отчет не попадет в статистику.

		Возвращает идентификатор нового сообщения.
		"""

		if minutes == None:
			minutes = 0

		return self.execute('select "eventNew"(%s,%s,%s,%s,%s,%s)',  None,  task_id,  html_text, MESSAGE_TYPE_REPORT,  message_id,  minutes)[0][0]

	def add_report_user(self,  task_id,  message_id,  html_text,  minutes, user_id, time):
		"""
		Добавляет сообщение типа отчет.

		Входнойые аргументы:
		message_id - идентификатор сообщения на которое пишется ответ
		html_text - текст сообщения в формате html.
		minutes - заявленое время отчета в минутах.

		Очень важнп устанавливать время в отчетах.
		Если minutes имеет занчение 0 или None, отчет не попадет в статистику.

		Возвращает идентификатор нового сообщения.
		"""

		if minutes == None:
			minutes = 0

		return self.execute('select "zEventNew"(%s,%s,%s,%s,%s,%s,%s)',  user_id,  task_id,  html_text, MESSAGE_TYPE_REPORT,  message_id,  minutes, time)[0][0]

	def add_resource_report(self,  task_id,  message_id,  resource_id,  html_text,  minutes):
		"""
		Добавляет сообщение типа отчет за ресурс.

		Входнойые аргументы:
		message_id - идентификатор сообщения на которое пишется ответ
		resource_id - идентификатор материального ресурса за который пишется отчет
		html_text - текст сообщения в формате html.
		minutes - заявленое время отчета в минутах.

		Возвращает идентификатор нового сообщения.
		"""
		return self.execute('select "eventNew"(%s,%s,%s,%s,%s,%s)',  resource_id,  task_id,  html_text, MESSAGE_TYPE_RESOURCE_REPORT,  message_id,  minutes)[0][0]


	def add_note(self,  task_id,  message_id,  html_text):
		"""
		Добавляет сообщение типа заметка.

		Входнойые аргументы:
		message_id - идентификатор сообщения на которое пишется ответ
		html_text - текст сообщения в формате html.

		Возвращает идентификатор нового сообщения.
		"""
		return self.execute('select "eventNew"(%s,%s,%s,%s,%s,%s)',  None,  task_id,  html_text, MESSAGE_TYPE_NOTE,  message_id,  None)[0][0]

	def add_note_user(self,  task_id,  message_id,  html_text, user_id, time):
		"""
		Добавляет сообщение типа заметка.

		Входнойые аргументы:
		message_id - идентификатор сообщения на которое пишется ответ
		html_text - текст сообщения в формате html.

		Возвращает идентификатор нового сообщения.
		"""
		return self.execute('select "zEventNew"(%s,%s,%s,%s,%s,%s,%s)',  user_id,  task_id,  html_text, MESSAGE_TYPE_NOTE,  message_id,  None, time)[0][0]


	def add_attachment(self,  message_id,  carga,  filename,  thumbnails,  description,  as_link, path = ''):
		"""
			Добавление вложения к сообщению

			Входнойые аргументы:
			message_id - идентификатор сообщения
			carga - объект класса cargador.Cargador, для импортирования файлов в файловое хранилище
			filename - полный путь до файла
			thumbnails - список путей до файлов эскизов (не больше трех).
								Размер эскизов должен быть 512x512. Формат JPG или PNG.
			description - пояснения(комментарии) к вложению
			as_link -  способ добавления файла к сообщению:
					True - файл добавляется как ссылка;
					False - файл добавляется как вложение, то есть импортируется в файловое хранилище(Cargador).

			# Генерация эскизов
			Если файл является изображением или видео, то можно добавить для него уменшенные эскизы.
			Можно добавить до 3-х эскизов (первый, средний, последний кадры).
			Для генерации эскизов можно использовать программу Mirada.
			Она постовляется вместе с дистрибутивом Cerebro. Можно использовать и другие программы для генерации,
			например, ffmpeg.
			::
				#Пример генерации эскизов с помощью Mirada.

				gen_path = os.path.dirname(filename) # В качестве директории для генерации эскизов возьмем директорию добавляемого файла

				mirada_path = './mirada' # путь до исполняемого файла программы Mirada

				# Запускаем мираду с необходимыми ключами
				res_code = subprocess.call([mirada_path, filename, '-temp', gen_path, '-hide'])
				#-temp - директория для генерации эскизов
				#-hide - ключ запуска мирады в скрытом режиме (без загрузки графического интерфейса) для генерации табнейлов.

				if res_code != 0:
					raise Exception("Mirada returned bad exit-status.\n" + mirada_path);


				#Ищем сгенерированные мирадой эскизы.
				#Имени эскиза формируется из имени файла, даты и времени генерации - filename_yyyymmdd_hhmmss_thumb[number].jpg
				#Например: test.mov_20120305_112354_thumb1.jpg - первый эскиз видео-файла test.mov

				thumbnails = list()
				for f in os.listdir(gen_path):
					if fnmatch.fnmatch(f, os.path.basename(filename) + '_*_thumb?.jpg'):
						thumbnails.append(gen_path + '/' + f)

				thumbnails.sort()
			::

			::
				#Пример генерации эскизов с помощью ffmpeg.
				#Для того, чтобы генерить эскизы с помощью ffmpeg, нужно заранее знать длительность видео,
				#чтобы корректно получить средний и последний кадры.
				#Возьмем к примеру ролик длительностью в 30 секунд.

				thumbnails = list() # список файлов для эскизов
				thumbnails.append(filename + '_thumb1.jpg')
				thumbnails.append(filename + '_thumb2.jpg')
				thumbnails.append(filename + '_thumb3.jpg')

				subprocess.call(['ffmpeg', '-i', filename, '-s', '512x512', '-an', '-ss', '00:00:00', '-r', 1, '-vframes', 1, '-y', thumbnails[0]])
				subprocess.call(['ffmpeg', '-i', filename, '-s', '512x512', '-an', '-ss', '15:00:00', '-r', 1, '-vframes', 1, '-y', thumbnails[1]])
				subprocess.call(['ffmpeg', '-i', filename, '-s', '512x512', '-an', '-ss', '30:00:00', '-r', 1, '-vframes', 1, '-y', thumbnails[2]])
				# Описание ключей вы можете посмотреть в документации к ffmpeg
			::
		"""

		#if os.path.exists(filename) == False:
		#	raise Exception('File ' + filename + ' not found')

		"""
		Приложение файла к сообщению состоит из двух этапов
		1 - добавление файла в файловое хранилище (Cargador)
			Этот этап пропускается, если файл прикладывается как ссылка
		2 - добавление записи(ей) в базу данных об этом файле
		"""
		hash = ''
		if as_link != True: 	# Если файл добавляется не как ссылка, добавляем его в Cargador и получаем его хеш
			if (carga) is None:
				raise Exception('Подключение к хранилищу отсутствует')
			# Запрос на получение текстового локатора задачи
			dset = set()
			dset.add(message_id)
			if path:
				task_url = path
			else:
				rtask_url = self.execute('select "getUrlBody_byTaskId_00"((select taskid from "eventQuery_08"(%s)))', dset)
				task_url = rtask_url[0][0]
			
			hash64 = carga.import_file(filename,  task_url) # Импортирование файла в хранилище
			hash = hash64_16(hash64)

			if hash == None or len(hash) == 0: # Если хеш не получен генерируем исключение
				raise Exception('Хеш не задан')


		tag = ATTACHMENT_TAG_FILE
		file_size = 0
		file_name = ''
		if as_link == True:
			tag = ATTACHMENT_TAG_LINK
			file_name = filename.replace('\\', '/')
		else:
			file_size = os.stat(filename).st_size
			file_name = os.path.basename(filename)

		"""
		Параметр tag нужен для определения вложения:
		dbtypes.ATTACHMENT_TAG_FILE - файл является вложением, то есть он находится в файловом хранилище Cargador и у него есть хеш
		dbtypes.ATTACHMENT_TAG_LINK - файл приложен как ссылка на файл(папку).

		Параметр file_size - размер файла в байтах. Для ссылки задаётся в 0.

		Параметр file_name - имя файла. Для ссылки должен быть полный путь до файла. Для вложения только базовое имя

		Параметр description - пояснения(комментарии) к приложенному файлу
		"""

		 # Получаем новый идентификатор для записи о файле в базу данных
		rnew_attach_id = self.execute('select "getNewAttachmentGroupID"()') # Выполняем запрос на новый идентификатор
		new_attach_id = rnew_attach_id[0][0]

		# Добавление записи о файле
		self.execute('select "newAtachment_00_"(%s::bigint, %s::integer, %s, %s::integer, %s::bigint, %s, %s)',
				message_id, new_attach_id, hash, tag, file_size, file_name, description) # Выполняем запрос для записи о файле
		"""
		Добавляемый файл может иметь несколько записей, например он может иметь уменшенные эскизы или рицензию.
		Для добавления дополнительных записей о файле должен использоватся тот же идентификатор, но различные теги.
		Если вы решите переделать скрипт для добавления нескольких файлов,
		то для каждого файла вам нужно получать новый идентификатор.
		"""
		if (carga) is None:
			print('Подключение к хранилищу отсутствует')
		else:
			if thumbnails != None and len(thumbnails) > 0:
				# Добавляем эскизы в файловое хранилище и получаем их хеши
				hashthumbs = list()
				for f in thumbnails:
					th_hash64 = carga.import_file(f,  'thumbnail.cache') # Импортирование эскиза файла в хранилище
					th_hash = hash64_16(th_hash64)
					hashthumbs.append(th_hash)

				# Добавляем хеши эскизов в базу данных
				for i in range(len(hashthumbs)):

					if i > 2:
						break

					tag = i+1 # Задаем тег для эскиза. 1 - первый эскиз, 2 - средний, 3 - последний

					# Добавление записи о эскизе
					self.execute('select "newAtachment_00_"(%s::bigint, %s::integer, %s, %s::integer, %s::bigint, %s, %s)',
							message_id, new_attach_id, hashthumbs[i], tag, 0, '', '') # Выполняем запрос для записи о эскизе
					"""
						Такие параметры как размер, имя файла и пояснения для эскизов не нужны, поэтому они забиваются пустыми полями
					"""

		return new_attach_id

	def project_tags(self,  project_id):
		"""
		:param int project_id: project ID.
		:returns: project tags table. The table contains all of the tags that can be set on project tasks.

		The table fields are described in the module dbtypes: :py:const:`TAG_DATA_...<py_cerebro.dbtypes.TAG_DATA_>`		
		"""		
		return self.execute('select * from "tagSchemaList_byPrj"(%s)',  project_id)
	
	def tag_enums(self,  tag_id):
		"""
		:param int tag_id: tag ID.
		:returns:  tag enumeration table. The table contains enumerations that can be set as the tag value.

		The table fields are described in the module dbtypes: :py:const:`TAG_ENUM_DATA_...<py_cerebro.dbtypes.TAG_ENUM_DATA_>`		
		"""		
		return self.execute('select * from "tagEnumList"(%s, false)',  tag_id)

	def task_set_tag_enum(self,  task_id,  enum_id,  is_set):
		"""
		:param task_id: task ID(s).
		:type task_id: int, set(int, ) or list(int, )
		:param enum_id: enumeration ID(s).
		:type enum_id: int, set(int, ) or list(int, )
		:param bool is_set: enumeration set / removed parameter.

		Sets or removes tag value of enumeration or multiple enumeration type for a task(s).
		"""
		
		tasks = self.execute('select "tagTaskSetEnum_a"(%s,%s,%s)',  get_val_by_type(enum_id),  get_val_by_type(task_id),  is_set)

		ids = set()
		for task in tasks:              
			ids.add(task[0])

		return ids

	def task_set_tag_float(self,  task_id,  tag_id,  value):
		"""
		:param task_id: task ID(s).
		:type task_id: int, set(int, ) or list(int, )
		:param int tag_id: tag ID.
		:param int value: tag value.

		Sets tag value of floating-point number type for a task(s).	
		"""
		
		tasks = self.execute('select "tagTaskSetReal_a"(%s,%s,%s)',  tag_id,  get_val_by_type(task_id), value)

		ids = set()
		for task in tasks:              
			ids.add(task[0])

		return ids
	
	def task_set_tag_int(self,  task_id,  tag_id,  value):
		"""
		:param task_id: task ID(s).
		:type task_id: int, set(int, ) or list(int, )
		:param int tag_id: tag ID.
		:param int value: tag value.

		Sets tag value of integer number type for a task(s).	
		"""
		
		tasks = self.execute('select "tagTaskSetInt_a"(%s,%s,%s)',  tag_id,  get_val_by_type(task_id), value)

		ids = set()
		for task in tasks:              
			ids.add(task[0])

		return ids

	def task_set_tag_string(self,  task_id,  tag_id,  value):
		"""
		:param task_id: task ID(s).
		:type task_id: int, set(int, ) or list(int, )
		:param int tag_id: tag ID.
		:param int value: tag value.

		Sets tag value of string type for a task(s).	
		"""
		
		tasks = self.execute('select "tagTaskSetStr_a"(%s,%s,%s)',  tag_id,   get_val_by_type(task_id), value)

		ids = set()
		for task in tasks:              
			ids.add(task[0])

		return ids
	
	def task_tag_reset(self,  task_id,  tag_id):
		"""
		:param task_id: task ID(s).
		:type task_id: int, set(int, ) or list(int, )
		:param int tag_id: tag ID.

		Removes tag value from a task(s).	
		"""
		
		tasks = self.execute('select "tagTaskReset_a"(%s,%s)',  tag_id,  get_val_by_type(task_id))

		ids = set()
		for task in tasks:              
			ids.add(task[0])

		return ids

	def task_tag_enums(self,  task_id,  tag_id):
		"""
		:param int task_id: task ID.
		:param int tag_id: tag ID.
		:returns: table of tag enumerations set on a task.

		The table fields are described in the module dbtypes: :py:const:`TASK_TAG_ENUM_...<py_cerebro.dbtypes.TASK_TAG_ENUM_>`
		"""
		return self.execute('select * from "tagTaskEnums"(%s,%s)',  task_id, tag_id)
	
	def task_tags(self,  task_id):
		"""
		:param int task_id: task ID.
		:returns: table of tag values set on a task.

		The table fields are described in the module dbtypes: :py:const:`TASK_TAG_DATA_...<py_cerebro.dbtypes.TASK_TAG_DATA_>`
		"""
		return self.execute('select * from "tagTaskList"(%s)',  task_id)

	def task_by_url(self,  url):
		"""
		:param string url: url of task.
		:returns: task ID.

		Return task ID by url. Url example: '/Test project/test'
		"""
		id = self.execute('select * from "getTaskID_byURL"(%s)', url)
		if len(id) == 1:
			return id[0]
			
		return None



