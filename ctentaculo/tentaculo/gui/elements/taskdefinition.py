# -*- coding: utf-8 -*-
from tentaculo.gui import style

from tentaculo.Qt.QtGui import *
from tentaculo.Qt.QtCore import *
from tentaculo.Qt.QtWidgets import *


class TaskDefinition(QFrame):

	def __init__(self, parent = None):
		super(self.__class__, self).__init__(parent = parent)
		self.initUI()
		self.initStyle()

	def initStyle(self):
		styler = style.Styler()
		styler.initStyle(self)

	def initUI(self):
		self.setFrameShape(QFrame.StyledPanel)
		self.setFrameShadow(QFrame.Raised)
		self.setObjectName("tasksDescr")

		verticalLayout = QVBoxLayout(self)
		verticalLayout.setContentsMargins(20, 10, 10, 10)
		verticalLayout.setSpacing(10)

		label = QLabel("TASK DEFINITION", self)

		self.tb_taskDescr = QTextBrowser(self)
		self.tb_taskDescr.setOpenExternalLinks(True)
		self.tb_taskDescr.document().setDocumentMargin(0)

		verticalLayout.addWidget(label)
		verticalLayout.addWidget(self.tb_taskDescr)

		self.setLayout(verticalLayout)

	def clearTask(self):
		self.tb_taskDescr.clear()

	def setTask(self, task = None):
		if task is None: return False

		#self.tb_taskDescr.setPlainText(QTextDocumentFragment.fromHtml(task["definition"]).toPlainText())
		text = task["definition"] + '<br/>'
		for msg in task["messages"]:
			text = text + '<b>' +  msg['author'] + ' ' + msg['date'] + '</b><br/>' + msg['msg'] + '<br/><br/>'
		self.tb_taskDescr.setHtml(text)

		return True
