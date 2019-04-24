# -*- coding: utf-8 -*-
import os

import logging
from logging.handlers import TimedRotatingFileHandler

from tentaculo import Qt, version
from tentaculo.core import capp, utils

# logger
# WARNING: This is SINGLETON
class CLogger(object):
	# singleton
	__instance = None

	log = None

	def __new__(cls, *args, **kwargs):
		if not isinstance(cls.__instance, cls):
			cls.__instance = super(CLogger, cls).__new__(cls, *args, **kwargs)
			cls.__instance()
		return cls.__instance

	def __call__(self):
		self.init_logger()

	def init_logger(self):
		if self.log == None:
			log_path = utils.tempdir()

			if not os.path.exists(log_path):
				os.makedirs(log_path)

			handler = TimedRotatingFileHandler(log_path + '/' + version.APP_SHORT_NAME + '.log.txt', when='midnight', interval=1, backupCount=7)
			formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
			handler.setFormatter(formatter)

			self.log = logging.getLogger(version.APP_SHORT_NAME)

			self.log.addHandler(handler)

			if capp.DEBUG:
				self.log.setLevel(logging.DEBUG)
			else:
				self.log.setLevel(logging.INFO)

			self.log.info('Start %s version %s', version.APP_NAME, version.APP_VERSION)
			self.log.info('Application: %s', capp.HOST_NAME)
			self.log.info('Qt binding: %s', Qt.__binding__)
