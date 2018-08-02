# -*- coding: utf-8 -*-
import os

from tentaculo.core import jsonio

from tentaculo.Qt.QtGui import *

class Styler(object):

	__style_source = "tentaculo.qss"
	__style_vars = "CerebroDark.json"
	__style_comp = "Style.qss"
	__style_res_var = "@resDir"

	__instance = None

	is_loaded = False
	dir_res = None
	dir_style = None
	final_style = ""
	
	def __new__(cls, *args, **kwargs):
		if not isinstance(cls.__instance, cls):
			cls.__instance = super(Styler, cls).__new__(cls, *args, **kwargs)
			cls.__instance()
		return cls.__instance

	def __call__(self, output_to_file = False):
		self.initFiles(output_to_file)

	def initFiles(self, output_to_file = False):
		self.is_loaded = True
		self.final_style = ""

		dir_self = os.path.dirname(os.path.realpath(__file__))
		self.dir_style = os.path.normpath(os.path.join(dir_self, "styles")).replace("\\","/")
		self.dir_res = os.path.normpath(os.path.join(dir_self, "../resources")).replace("\\","/")

		style = os.path.join(self.dir_style, self.__style_source)
		if os.path.exists(style):
			style_source = ""
			with open(style, 'r') as file:
				style_source = file.read()

			vars = os.path.join(self.dir_style, self.__style_vars)
			style_vars = jsonio.read(vars)
			if style_vars is not None:
				for name, value in style_vars.items():
					style_source = style_source.replace(name, value)

			self.final_style = style_source.replace(self.__style_res_var, str(self.dir_res))

			if output_to_file:
				style_output = os.path.join(self.dir_style, self.__style_comp)
				with open(style_output, 'w') as file:
					file.write(self.final_style)

			# Fonts
			# QFontDatabase.applicationFontFamilies(i)
			QFontDatabase.addApplicationFont(os.path.join(self.dir_res, "fonts", "HelveticaNeue.ttf"))
			QFontDatabase.addApplicationFont(os.path.join(self.dir_res, "fonts", "HelveticaNeue-Medium.ttf"))
			QFontDatabase.addApplicationFont(os.path.join(self.dir_res, "fonts", "HelveticaNeue-Bold.ttf"))

			self.is_loaded = True

	def initStyle(self, object = None):
		if object is None or not self.is_loaded: return False

		object.setStyleSheet(self.final_style)

		return True
