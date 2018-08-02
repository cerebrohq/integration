# -*- coding: utf-8 -*-

'''
/bigtrip
		/assets/objs/bear_hut
							/shade
							/proxy
							/model


Структура

Структура для создания новых файлов и папок в о вложении
Сделаем это все пока в json конфиге. Или даже можно пока прямо в питон конфиге. Возможно удобнее будет переделать списки в словари.
При создании нового файла, нужно будет создавать всю структуру папок, если их нет.

config
	['project_path']
		[0]
			['project']
				['project_name']
				['windows']

{
	project_path : //пути до папки проекта, без имени самого проекта, для разных операционных систем
	[
		project:
		{
			project_name : 'имя проекта' // Пустое поле означает любой проект, кроме тех что заданы в других элементах списка

			windows: 'путь' // например //server/projects
			linux: 'путь' 	// например /server/projects
			macos: 'путь'  	// например /Volumes/projects
		}
	]

	file_path : пути до файлов
	[
		folder:
		{
			folder_path: 'путь папки' форматированный путь. Начало пути от проекта (без имени самого проекта),
			// Пустое поле означает любой проект, кроме тех что заданы в других элементах списка

			version: 'путь до папки с версиями'   				// форматированный путь (формат описан ниже)
			publish: ''путь до папки с опубликованной версией'  // форматированный путь
			preview:  'путь до превью файлов' 					// форматированный путь
			name: 'имя файла' // форматированное имя
			version: 'префикс номера версии с количеством цифр по умолчанию' // количество цифр задается нулями, например '_v00', означает, что нумерация версий будет 01, 02 и тд. (Обработать, если будет больше версий чем цифр заданных в этом формате)
		}
	]
}

Форматированный путь и форматированное имя может содержать следующее переменные:
$(url[0]), $(url[1]) ... $(url[X]), – где X  - уровень вложенности задачи. Например $(url[0]) - имя проекта, $(url[1]) - имя подзадачи проекта и тд.
$(app_name) - имя приложения, в котором работает интеграция
$(version) - номер версии с префиксом

Пример конфига для петрушки


{
	# list of dicts - projects
	project_path :	# может быть несколько, должно совпадать с тем что в церебре, извлекается из пути сплитом и первый элемент - проект
	[
		project:
		{
			project_name : ''

			windows: '//alpha/prj'
			linux: '/alpha/prj'
			macos: '/Volumes/prj'
		}
	]
	# list of dicts - folders
	file_path
	[
		folder:
		{
			folder_path: 'assets'

			version: '$(url[0])/$(url[1])/$(url[2])/$(url[3])/versions'
			publish: ''$(url[0])/$(url[1])/$(url[2])/$(url[3])'
			preview:  '$(url[0])/$(url[1])/$(url[2])/$(url[3])/preview'
			name: '$(url[3])_$(url[4])_$(ver)'
			ver: 'v00'
		},
		folder:
		{
			folder_path: 'shots' // тут пока теже значения что для ассетов, не помню какая там структура

			version: '$(url[0])/$(url[1])/$(url[2])/$(url[3])/versions'
			publish: ''$(url[0])/$(url[1])/$(url[2])/$(url[3])'
			preview:  '$(url[0])/$(url[1])/$(url[2])/$(url[3])/preview'
			name: '$(url[3])_$(url[4])_$(ver)'
			ver: 'v00'
		}
	]
}
'''


import sys, os, platform, shutil, re, time, subprocess
from ctentaculo.client import core

class Config():
	'''
	1. initialize with defaults
	2. if filename given - read config from file
	3. dict = config.translate(task)
	'''


	def __init__(self, fname = None):
		'''
		Always tries to read the default/given filename
		Always creates default configuration
		'''
		self.clear()
		if fname is not None:
			self.fname = fname
		if self.fname is not None:
			self.read()


	def show(self):
		for key in self.config:
			print(key)
			print(self.config[key])


	def clear(self):
		self.fname = 'site_config_default'
		self.config = {}
		self.config[r'scripts'] = []
		self.config[r'project_path'] = []
		self.config[r'file_path'] = []
		self.paths = {}
		self.createDefaults()


	# config file I/O
	def setFile(self, fname = None):
		if fname is None: return
		self.fname = fname


	def write(self):
		if self.fname is None: return False
		core.jsonio.write(self.fname, self.config)		


	def read(self):
		if self.fname is None: return False
		cfg = core.jsonio.read(self.fname)
		if cfg is None:
			return False
		self.config = cfg
		return True


	def addScripts(self):
		'''
		Adds 'scripts' section to self.config
		'''
		scripts = {}
		scripts['maya_open_pre'] = ''
		scripts['maya_open_post'] = ''
		scripts['maya_save_pre'] = ''
		scripts['maya_save_post'] = ''
		scripts['houdini_open_pre'] = ''
		scripts['houdini_open_post'] = ''
		scripts['houdini_save_pre'] = ''
		scripts['houdini_save_post'] = ''
		scripts['nuke_open_pre'] = ''
		scripts['nuke_open_post'] = ''
		scripts['nuke_save_pre'] = ''
		scripts['nuke_save_post'] = ''
		self.config['scripts'] = scripts


	def addProject(self, project_name = None, windows = None, linux = None, macos = None):
		project = {r'project_name' : project_name, r'windows' : windows, r'linux' : linux, r'macos' : macos}
		self.config[r'project_path'].append(project)
		return project


	def addFolder(self, folder_path = None, version = None, publish = None, preview = None, name = None, ver_prefix = None, ver_padding = None, ver = None):
		folder = {r'folder_path' : folder_path, r'version' : version, r'publish' : publish, r'preview' : preview, r'name' : name, r'ver_prefix' : ver_prefix, r'ver_padding' : ver_padding, r'ver' : ver}
		self.config[r'file_path'].append(folder)
		return folder


	def createDefaults(self):
		'''
		Adds default configuration to config dict
		creates 2 variables with default folder and project
		'''
		self.defProj = self.addProject(project_name = '', windows = "c:\\", linux = "~/", macos = "~/")
		self.defFolder = self.addFolder(
										folder_path = '',
										version = '$(url[0])/$(url[1])/$(url[2])/$(url[3])/versions',
										publish = '$(url[0])/$(url[1])/$(url[2])/$(url[3])',
										preview = '$(url[0])/$(url[1])/$(url[2])/$(url[3])/preview',
										name = '$(url[3])_$(url[4])',
										ver_prefix = 'v',
										ver_padding = '2',
										ver = '0'
										)
		self.addScripts()


	def createPetrushka(self):
		self.addProject(project_name = r'bigtrip', windows = r'//alpha/prj', linux = r'~/', macos = r'~/')
		self.addFolder(
						folder_path = 'assets',
						version = '$(url[0])/$(url[1])/$(url[2])/$(url[3])/versions',
						publish = '$(url[0])/$(url[1])/$(url[2])/$(url[3])',
						preview = '$(url[0])/$(url[1])/$(url[2])/$(url[3])/preview',
						name = '$(url[3])_$(url[4])',
						ver_prefix = 'v',
						ver_padding = '2',
						ver = '0'
						)
		self.addFolder(
						folder_path = 'shots',
						version = '$(url[0])/$(url[1])/$(url[2])/$(url[3])/versions',
						publish = '$(url[0])/$(url[1])/$(url[2])/$(url[3])',
						preview = '$(url[0])/$(url[1])/$(url[2])/$(url[3])/preview',
						name = '$(url[3])_$(url[4])',
						ver_prefix = 'v',
						ver_padding = '2',
						ver = '0'
						)
		self.addScripts()


	def getTaskProject(self, proj = None):
		if proj is None: return self.defProj
		curProj = None
		for p in self.config.get(r'project_path'):
			if proj == p.get('project_name'):
				return p
		# if not found - return default project
		return self.defProj


	def getTaskFolder(self, folder = None):
		if folder is None: return self.defFolder
		curFolder = None
		for folder in self.config['file_path']:
			if folder == folder.get(r'folder_path'):
				return folder
		# if not found - return default folder
		return self.defFolder


	def translate(self, task = None, in_version = None):
		'''
		/Cerebro/tentaculo/Этап 3/4. Настройки структуры/Реализация
		task name should go in _as is_, without filenames or such things
		if no project or task name exists: it will use default '' names which _should_ exist in config
		'''
		if task is None: return None
		#task = task.decode(r'utf-8')
		task_parts = re.split('/', task)
		if task_parts is None or len(task_parts) < 2: return None
		# del empties
		for i, f in reversed(list(enumerate(task_parts))):
			if f == '' or len(f) == 0:
				del task_parts[i]

		# resulting copy with path
		path_parts = task_parts
		# here we have curProj and curFolder vars
		curProj = self.getTaskProject(path_parts[0])
		curFolder = self.getTaskFolder(path_parts[-1])
		# adding root path to the first element of path_parts
		project_root = curProj.get(core.hostapp.getHost())
		path_parts[0] = os.path.join(project_root, path_parts[0])

		# processing all entries in curFolder dict
		self.paths = {}
		for key in curFolder:
			url = curFolder.get(key)
			if len(url) == 0: continue	# empty name workaround
			cntr = 0
			for p in path_parts:
				src = r'$(url[' + str(cntr) + r'])'
				url = url.replace(src, p)
				cntr += 1
			# replace the rest of tokens(if any) for the case we have wrong config file
			url = re.sub(r'\$\(url\[\d+\]\)', '', url)
			# and cleanup leftovers
			url = url.replace("\\", r"/")
			url = url.replace("//", "/")
			url = url.replace("__", "_")
			if url.startswith("/"):
				url = "/" + url
			self.paths[key] = url
		return self.paths



	def makeFolders(self, dict = None):
		'''
		Creates all the folders starting from shortest to longest with lines containing slashes
		'''
		badflag = 0
		# use self.paths if no args given
		d = dict
		if d is None:
			d = self.paths
		sdict = sorted(d.values())
		for val in sdict:
			if '/' in val or '\\' in val:
				try:
					os.makedirs(val)
				except OSError as e:
					#if e.errno != errno.EEXIST:
					badflag += 1
		if badflag > 0: return False
		return True


	def makeTaskFolders(self, task = None):
		if task is None: return False
		dict = self.translate(task)
		self.makeFolders(dict)















if __name__ == "__main__":
	c = Config('site_config_petrushka')
	c.createPetrushka()
	c.write()

