# -*- coding: utf-8 -*-

import os, subprocess

from tentaculo.core import capp, utils, fmanager, config, vfile
from tentaculo.api.icerebro import db
from tentaculo.gui import style, wapp

from tentaculo.Qt.QtGui import *
from tentaculo.Qt.QtCore import *
from tentaculo.Qt.QtWidgets import *
from tentaculo.Qt import QtCompat


class w_sendmsg(QDialog):
	NAME = 'SEND_MESSAGE_WINDOW'
	TITLE = 'Send message to selected task'

	refresh = Signal()

	parent = None
	task_id = None
	attachments = {}

	def __init__(self, parent = None):
		super(self.__class__, self).__init__(parent = parent)
		self.conn = db.Db()
		self.fman = fmanager.FManager()
		self.config = config.Config()
		self.fvers = vfile.VFile(None)
		self.initUI()
		self.initStyle()
		self.clear()

	def initStyle(self):
		styler = style.Styler()
		styler.initStyle(self)

	def clear(self):
		self.task_id = None
		self.te_message.clear()
		self.attachments = {}
		self.update_files()

	def send_message(self):
		msg = utils.string_unicode(self.te_message.toPlainText())

		if len(msg) == 0 or self.task_id is None: return False

		send_links = {}
		send_attach = {}
		for fpath, as_link in self.attachments.items():
			fpath = os.path.normpath(fpath)
			# Generate thumbnails
			thumbs = self.fman.z_thumbnails(fpath)

			if as_link:
				send_links[fpath] = thumbs
			else:
				send_attach[fpath] = thumbs
		
		newmsg = self.conn.send_message(self.task_id, msg, send_links, send_attach)

		if newmsg is not None:
			self.refresh.emit()
			self.clear()
			self.stop()
			return True

		return False

	def add_files(self, as_link):
		files = wapp.file("Select files to add", self.fvers.default_dir())
		if files is not None:
			for file in files:
				self.attachments[file] = as_link
			self.update_files()

	def update_files(self):
		self.tableWidget.clear()
		self.tableWidget.setRowCount(len(self.attachments))
		for i, fpath in enumerate(self.attachments):
			itmType = QTableWidgetItem("{0}".format(u"LINK" if self.attachments[fpath] else u"ATTACH"))
			itmPath = QTableWidgetItem(fpath)
			itmType.setFlags(itmType.flags() & ~Qt.ItemIsEditable)
			itmPath.setFlags(itmPath.flags() & ~Qt.ItemIsEditable)
			self.tableWidget.setItem(i, 0, itmType)
			self.tableWidget.setItem(i, 1, itmPath)

	def __popupAt(self, pos):
		index = self.tableWidget.indexAt(pos)
		if not index.isValid(): return

		menu = QMenu()
		styler = style.Styler()
		styler.initStyle(menu)

		acts = []
		menu_options = ["Delete", "Change type", "Show in Explorer"]
		for opt in menu_options:
			if opt is None:
				menu.addSeparator()
			else:
				action = menu.addAction(opt)
				acts.append(action)
		try:
			ind = acts.index(menu.exec_(self.tableWidget.viewport().mapToGlobal(pos)))
			item = self.tableWidget.item(index.row(), 1).text()
			if ind == 0:
				self.attachments.pop(item)
				self.update_files()
			elif ind == 1:
				self.attachments[item] = not self.attachments[item]
				self.update_files()
			elif ind == 2:
				utils.show_dir(item)

		except ValueError:
			pass

	def initUI(self):
		self.setObjectName(self.NAME)
		self.setWindowTitle(self.TITLE)
		self.setMinimumSize(400, 600)

		verticalLayout = QVBoxLayout(self)
		verticalLayout.setSpacing(10)
		verticalLayout.setContentsMargins(20, 20, 20, 20)
		verticalLayout.setAlignment(Qt.AlignHCenter)

		label = QLabel("MESSAGE TEXT", self)

		self.te_message = QTextEdit(self)
		self.te_message.setObjectName("message")
		self.te_message.setAcceptRichText(False)
		self.te_message.document().setDocumentMargin(0)
		self.te_message.textChanged.connect(lambda: self.pb_sendmsg.setEnabled(len(self.te_message.toPlainText())))

		if capp.QT5:
			self.te_message.setPlaceholderText("Type here...")

		horizontalLayout = QHBoxLayout()
		horizontalLayout.setSpacing(10)
		horizontalLayout.setContentsMargins(0, 0, 0, 0)

		lb_addfile = QLabel("Add file:", self)
		lb_addfile.setFixedWidth(50)

		pb_link = QPushButton("As link", self)
		pb_link.clicked.connect(lambda: self.add_files(True))
		pb_link.setObjectName("small")

		pb_upload = QPushButton("As attachment", self)
		pb_upload.clicked.connect(lambda: self.add_files(False))
		pb_upload.setObjectName("small")

		horizontalLayout.addWidget(lb_addfile)
		horizontalLayout.addWidget(pb_link)
		horizontalLayout.addWidget(pb_upload)
		horizontalLayout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

		self.tableWidget = QTableWidget(self)
		self.tableWidget.setObjectName("attach")
		self.tableWidget.setColumnCount(2)
		self.tableWidget.setMaximumHeight(80)
		self.tableWidget.setColumnWidth(0, 60)
		QtCompat.setSectionResizeMode(self.tableWidget.verticalHeader(), QHeaderView.ResizeToContents)
		self.tableWidget.verticalHeader().setDefaultSectionSize(20)
		self.tableWidget.verticalHeader().hide()
		self.tableWidget.horizontalHeader().setStretchLastSection(True)
		self.tableWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.tableWidget.horizontalHeader().setSortIndicator(0, Qt.DescendingOrder)
		self.tableWidget.horizontalHeader().hide()
		self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
		self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
		self.tableWidget.setShowGrid(False)
		self.tableWidget.setAlternatingRowColors(True)
		self.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
		self.tableWidget.customContextMenuRequested.connect(self.__popupAt)

		self.pb_sendmsg = QPushButton("SEND", self)
		self.pb_sendmsg.clicked.connect(self.send_message)
		self.pb_sendmsg.setEnabled(False)

		verticalLayout.addWidget(label)
		verticalLayout.addWidget(self.te_message)
		verticalLayout.addLayout(horizontalLayout)
		verticalLayout.addWidget(self.tableWidget)
		verticalLayout.addWidget(self.pb_sendmsg)

	def run(self, task_id):
		if task_id is not None:
			self.task_id = task_id
			self.fvers.setConfig(self.config.translate(self.conn.task(self.task_id)))
			self.exec_()

	def stop(self):
		self.accept()
