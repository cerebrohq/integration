# -*- coding: utf-8 -*-

import os, re

from tentaculo.core import capp

class VFile:

	def __init__(self, task_config, file_extension = None):
		self.setConfig(task_config, file_extension)

	def clear(self):
		self.base_name = None
		self.path_local = None
		self.path_version = None
		self.path_publish = None
		self.path_preview = None
		self.ver_prefix = None
		self.ver_padding = None
		self.extension = None

		self.__regexp = None

		self.is_empty = True
		self.has_versions = False
		self.versions = {}
		self.last_number = 0
		self.next_version = None
		self.publish = None
		self.local = None

	def setConfig(self, task_config, file_extension = None):
		self.clear()
		self.is_empty = not self.initData(task_config, file_extension)
		MAKE_I_REMEMBER_WHY_EXTENTION = None
		if not self.is_empty:
			self.findVersions()

	def initData(self, task_config = None, file_extension = None):
		if task_config is None: return False
		
		self.path_local = task_config.get("local", '')
		self.path_version = task_config.get("version", '')
		self.path_preview = task_config.get("preview", '')
		self.path_publish = task_config.get("publish", '')		
		self.base_name = task_config.get("name", None)
		self.ver_padding = int(task_config.get("ver_padding", 3))
		self.ver_prefix = task_config.get("ver_prefix", None)
		self.extension = capp.HOST_EXT[0] if file_extension is None else file_extension

		if self.base_name is None: return False

		self.__regexp = re.compile(u"{0}({1})(\d{{0,{2}}})({3})\Z".format(
			self.base_name,
			r"\w*" if self.ver_prefix is None else self.ver_prefix,
			4 if self.ver_padding is None else self.ver_padding,
			r"\.[a-zA-Z]+" if self.extension is None else self.extension
			))
		
		MAKE_PRINT_INFO_AND_DEBUG = None
		return True

	def findVersions(self):
		if self.is_empty: return False
		if os.path.exists(self.path_version):
			self.versions = { int(f.group(2)): f.group() for f in map(self.__regexp.match, os.listdir(self.path_version)) if f is not None and os.path.isfile(os.path.join(self.path_version, f.group())) }
		else:
			self.versions = {}
		self.has_versions = len(self.versions) > 0

		if self.has_versions:
			self.last_number = max(self.versions)

			m = self.__regexp.match(self.versions[self.last_number])
			if self.ver_prefix is None: self.ver_prefix = m.group(1)
			if self.extension is None: self.extension = m.group(3)
			if self.ver_padding is None: self.ver_padding = len(m.group(2))

		self.next_version = u"{0}{1}{2}{3}".format(
			self.base_name,
			"" if self.ver_prefix is None else self.ver_prefix,
			str(self.last_number + 1).zfill(2 if self.ver_padding is None else self.ver_padding),
			self.extension
			)
		self.publish = u"{0}{1}".format(self.base_name, self.extension)
		self.local = u"{0}{1}local{2}".format(self.base_name, "" if self.ver_prefix is None else self.ver_prefix, self.extension)

		return self.has_versions

	def file_version(self, file_path):
		ver_num = None
		if self.has_versions:
			file_name = os.path.basename(file_path)

			for i, v in self.versions.items():
				if v == file_name:
					ver_num = i
					break

		return ver_num

	def file_name(self, file_path):
		if file_path is None: return None

		file_name = os.path.basename(file_path)
		base_name = u""

		if self.ver_prefix is not None and self.ver_prefix in file_name:
			regexp = re.compile(u"(\w+){0}\d{{0,{1}}}{2}\Z".format(
				self.ver_prefix,
				4 if self.ver_padding is None else self.ver_padding,
				r"\.[a-zA-Z]+" if self.extension is None else self.extension
				))
			m = regexp.match(file_name)
			if m is not None:
				base_name = m.group(1)
		else:
			base_name = os.path.splitext(file_name)[0]

		return base_name

	def next_version_path(self):
		if self.is_empty or len(self.path_version) == 0: return None

		return os.path.join(self.path_version, self.next_version)

	def publish_path(self):
		if self.is_empty or len(self.path_publish) == 0: return None

		return os.path.join(self.path_publish, self.publish)

	def local_path(self):
		if self.is_empty or len(self.path_local) == 0: return None

		return os.path.join(self.path_local, self.local)
