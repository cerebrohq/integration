# -*- coding: utf-8 -*-
from tentaculo.gui import style

from tentaculo.api.icerebro import db
from tentaculo.core import clogger, config

from tentaculo.Qt.QtGui import *
from tentaculo.Qt.QtCore import *
from tentaculo.Qt.QtWidgets import *


class TaskControls(QFrame):
	publish = Signal(bool)

	__selected_task_id = None

	def __init__(self, task_select = False, parent = None):
		super(self.__class__, self).__init__(parent = parent)
		self.log = clogger.CLogger().log
		self.conn = db.Db()
		self.config = config.Config()
		self.initUI(task_select)
		self.initStyle()
		self.clearTask()

	def initStyle(self):
		styler = style.Styler()
		styler.initStyle(self)

	def initUI(self, task_select = False):
		self.setFrameShape(QFrame.StyledPanel)
		self.setFrameShadow(QFrame.Raised)
		self.setObjectName("tasksButtons")
		self.setFixedHeight(48)

		horizontalLayout = QHBoxLayout(self)
		horizontalLayout.setContentsMargins(20, 10, 20, 10)
		horizontalLayout.setSpacing(10)

		horizontalSpacer = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
		
		self.pb_taskSave = QPushButton("Save as New Version", self)
		self.pb_taskSave.clicked.connect(lambda: self.publish.emit(False))
		self.pb_taskSave.setVisible(not task_select)
		

		self.pb_taskPublish = QPushButton("OK" if task_select else "Publish", self)
		self.pb_taskPublish.clicked.connect(lambda: self.publish.emit(True))
		
		horizontalLayout.addItem(horizontalSpacer)
		horizontalLayout.addWidget(self.pb_taskSave)
		horizontalLayout.addWidget(self.pb_taskPublish)

		self.setLayout(horizontalLayout)

	def clearTask(self):
		self.pb_taskSave.setEnabled(False)
		self.pb_taskPublish.setEnabled(False)
		self.__selected_task_id = None

	def setTask(self, task):
		if task is None: return False

		self.__selected_task_id = task["id"]

		enabled = self.config.task_valid(task)[0] and task["enabled_task"]

		self.pb_taskPublish.setEnabled(enabled)
		self.pb_taskSave.setEnabled(enabled)

		return True
