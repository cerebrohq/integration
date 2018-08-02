# -*- coding: utf-8 -*-
import os, time, datetime

from tentaculo.core import capp, shot, vfile, config, clogger, fmanager
from tentaculo.api.icerebro import db
from tentaculo.gui import style, wapp

from tentaculo.Qt.QtGui import *
from tentaculo.Qt.QtCore import *
from tentaculo.Qt.QtWidgets import *
from tentaculo.Qt import QtCompat

class w_createReport(QWidget):
	NAME = 'CREATE_REPORT_WINDOW'
	TITLE = 'Create Report'
	parent = None
	conn = None
	config = None
	shot = None
	fvers = None
	task = None
	task_id = None
	to_publish = False
	thumbs = []
	attachments = {}

	def __init__(self, taskid = None, to_publish = False, parent = None):
		capp.clearUI(self.NAME)
		super(self.__class__, self).__init__(parent = parent)
		self.setWindowFlags(Qt.Window)
		self.log = clogger.CLogger().log
		self.conn = db.Db()
		self.fman = fmanager.FManager()
		self.initStyle()
		self.initUI()
		self.initData(taskid, to_publish)

	def event(self, event):
		if event.type() == QEvent.WindowDeactivate:
			capp.focus_out()
		elif event.type() == QEvent.WindowActivate:
			capp.focus_in()
		return super(self.__class__, self).event(event)

	def initStyle(self):
		styler = style.Styler()
		styler.initStyle(self)

	def initData(self, taskid = None, to_publish = False):
		self.task_id = taskid
		self.to_publish = to_publish
		self.ver_thumb = None
		self.attachments = {}

		if self.to_publish:
			self.setWindowTitle("Publish")
			self.lb_header.setText("Publish")
			self.pb_publish.setText("Publish")
		else:
			self.setWindowTitle("Create Report")
			self.lb_header.setText("Report")
			self.pb_publish.setText("Report")

		self.te_report.document().setPlainText("")
		if not self.conn.connected:
			self.conn.login()
		if self.conn.connected:
			self.config = config.Config()
			file_name = capp.file_name(self.log)
			file_time = self.config.time_for_file(file_name)
			if file_time is not None:
				td = datetime.datetime.now() - file_time
				if td.days == 0: # 24h
					mins = td.seconds // 60
					if mins % 5 > 0:
						mins = mins // 5 * 5 + 5
					self.cb_time.setEditText("{0}{1}".format(str(mins // 60).zfill(2), str(mins).zfill(2)))
			# Set file task
			if self.task_id is None:
				self.task_id = self.config.task_for_file(file_name)
				
			self.fvers = vfile.VFile(self.config.translate(self.conn.task(self.task_id)))
			self.shot = shot.Shot(self)

		self.taskSet(self.task_id)
		self.screenTake()
		self.log.info("Report task selected: %s", self.task_id)

	def taskSet(self, task_id):		

		self.task = self.conn.task(task_id)
		self.pb_publish.setEnabled(False)
		
		if self.task is not None:
			self.fvers.setConfig(self.config.translate(self.task))
			self.task_id = task_id
			if self.config.task_valid(self.task)[0]:
				self.pb_publish.setEnabled(self.fvers.publish_path() is not None or self.fvers.next_version_path() is not None)
				self.lb_taskName.setText(self.task["name"])
				self.lb_taskPath.setText(self.task["path_repr"])

				thumb = QImage(self.task["thumbnail"]).scaled(73, 40, Qt.KeepAspectRatioByExpanding)

				if thumb.isNull():
					thumb = QImage(capp.getResDir("image.png"))

				self.lb_taskThumb.setPixmap(QPixmap.fromImage(thumb))
			
				self.cb_taskFile.clear()
				self.cb_taskFile.lineEdit().setReadOnly(not self.task["name_editable"])
				if not self.fvers.is_empty:
					ver = self.fvers.next_version if self.fvers.next_version_path() is not None else self.fvers.publish
					self.le_taskFile.setText(ver[len(self.fvers.base_name):])
					self.cb_taskFile.addItems(self.task["name_list"])
					if self.cb_taskFile.findText(self.fvers.base_name) == -1 and len(self.fvers.base_name) > 0:
						self.cb_taskFile.addItem(self.fvers.base_name)
					if capp.QT5:			
						self.cb_taskFile.setCurrentText(self.fvers.base_name)
					else:
						self.cb_taskFile.setEditText(self.fvers.base_name)
					
				else:
					self.le_taskFile.clear()

				self.updateStatusList()

	def update_savename(self):
		self.config.set_task_filename(self.task_id, self.cb_taskFile.currentText())
		self.fvers.setConfig(self.config.translate(self.task))
		self.pb_publish.setEnabled(self.fvers.publish_path() is not None or self.fvers.next_version_path() is not None)
		ver = self.fvers.next_version if self.fvers.next_version_path() is not None else self.fvers.publish
		if not self.fvers.is_empty:
			self.le_taskFile.setText(ver[len(self.fvers.base_name):])
		else:
			self.le_taskFile.clear()

	def updateStatusList(self):
		self.cb_status.clear()
		self.statuses = self.conn.task_statuses(self.task_id)
		task = self.conn.task(self.task_id)
		if task is not None:
			ind = -1
			for i, st in enumerate(self.statuses):
				if task["status"] == st[0]:
					ind = i
				self.cb_status.addItem(st[0])
			self.cb_status.setCurrentIndex(ind)

	def openProjectsBrowser(self):
		from tentaculo.gui import taskwindow
		taskwnd = taskwindow.w_taskwindow(True)
		taskwnd.task_set.connect(lambda: self.taskSet(taskwnd.selected_task))
		taskwnd.run()

	def add_files(self, as_link):
		files = wapp.file("Select files to add")
		if files is not None:
			for file in files:
				self.attachments[file] = as_link
			self.update_files()

	def update_files(self):
		self.tableWidget.clear()
		self.tableWidget.setRowCount(len(self.attachments))
		for i, fpath in enumerate(self.attachments):
			self.tableWidget.setItem(i, 0, QTableWidgetItem("{0}".format(u"LINK" if self.attachments[fpath] else u"ATTACH")))
			self.tableWidget.setItem(i, 1, QTableWidgetItem(fpath))

	def __popupAt(self, pos):
		index = self.tableWidget.indexAt(pos)
		if not index.isValid(): return

		menu = QMenu()
		styler = style.Styler()
		styler.initStyle(menu)

		acts = []
		menu_options = ["Delete", "Change type"]
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

		except ValueError:
			pass

	def sendReport(self):
		if self.task is None:
			self.log.error('No select task to publish')
			return False

		res = False

		opname = 'Save as New Version'
		if self.to_publish:
			opname = 'Publish'	

		self.log.info('%s started...', opname)
		self.log.info('Task: %s', self.task["path"] + self.task["name"])

		# Status
		status = None
		if self.cb_status.currentIndex() >= 0:
			status = self.statuses[self.cb_status.currentIndex()][1]
		# Text
		text = self.te_report.toPlainText()
		# Time
		h, m = self.cb_time.currentText().split("h ")
		h = int(h) if len(h) > 0 else 0
		m = m.split("m")[0]
		m = int(m) if len(m) > 0 else 0
		work_time = h * 60 + m
		try:
			processdata = {"local_file_path": u"", "version_file_path": u"", "publish_file_path": u"", "report": {}, "attachments": {}, "links": {}}
			processdata["report"]["plain_text"] = text
			processdata["report"]["work_time"] = work_time
			for fpath, as_link in self.attachments.items():
				if as_link:
					processdata["links"][fpath] = []
				else:
					processdata["attachments"][fpath] = []

			version_file = None
			if self.to_publish and self.fvers.publish_path() is not None:
				version_file = self.fman.publish(self.task, processdata, status, self.ver_thumb)
			else:
				version_file = self.fman.version(self.task, processdata, status, self.ver_thumb)

			if version_file:
				self.log.info('%s has been successfully.', opname)
				res = True

			self.conn.refresh_task(self.task_id)
			self.stop()
		except Exception as err:
			wapp.error(capp.string_unicode(str(err)))
		return res

	def screenTake(self):
		self.screenClear()
		self.shot.take()
		if self.shot.img is not None:
			self.lb_screen.setPixmap(self.shot.img.scaled(400, 200, Qt.KeepAspectRatioByExpanding))
			self.ver_thumb = self.shot.fname

	def screenClear(self):
		self.ver_thumb = None
		self.shot.clear()
		self.lb_screen.clear()

	def initUI(self):
		#window init start
		self.setWindowFlags(Qt.Window)
		self.setObjectName(self.NAME)
		self.setWindowTitle('Cerebro: Create Report')
		self.resize(800, 600)
		#window init end

		verticalLayout_8 = QVBoxLayout(self)
		verticalLayout_8.setSpacing(0)
		verticalLayout_8.setContentsMargins(0, 0, 0, 0)

		frame = QFrame(self)
		frame.setFrameShape(QFrame.StyledPanel)
		frame.setFrameShadow(QFrame.Raised)
		frame.setObjectName("publishHeader")
		frame.setFixedHeight(48)

		verticalLayout = QVBoxLayout(frame)
		verticalLayout.setSpacing(0)
		verticalLayout.setContentsMargins(20, 0, 20, 0)

		self.lb_header = QLabel("Publish", frame)
		self.lb_header.setObjectName("lightHeader")

		verticalLayout.addWidget(self.lb_header)

		frame_2 = QFrame(self)
		frame_2.setFrameShape(QFrame.StyledPanel)
		frame_2.setFrameShadow(QFrame.Raised)
		frame_2.setObjectName("publishTask")
		frame_2.setFixedHeight(96)

		verticalLayout_3 = QVBoxLayout(frame_2)
		verticalLayout_3.setSpacing(10)
		verticalLayout_3.setContentsMargins(20, 10, 20, 20)

		label_2 = QLabel("TASK", frame_2)

		horizontalLayout_2 = QHBoxLayout()
		horizontalLayout_2.setSpacing(10)
		horizontalLayout_2.setContentsMargins(0, 0, 0, 0)

		self.lb_taskThumb = QLabel(frame_2)
		self.lb_taskThumb.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
		self.lb_taskThumb.setFixedSize(73, 40)

		verticalLayout_2 = QVBoxLayout()
		verticalLayout_2.setSpacing(0)
		verticalLayout_2.setContentsMargins(0, 0, 0, 0)

		self.lb_taskName = QLabel(frame_2)
		self.lb_taskName.setObjectName("header")

		horizontalLayout = QHBoxLayout()
		horizontalLayout.setSpacing(0)
		horizontalLayout.setContentsMargins(0, 0, 0, 0)

		self.lb_taskPath = QLabel(frame_2)
		self.lb_taskPath.setObjectName("active")

		horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

		pushButton = QPushButton("Choose another task", frame_2)
		pushButton.clicked.connect(self.openProjectsBrowser)
		pushButton.setObjectName("small")

		horizontalLayout.addWidget(self.lb_taskPath)
		horizontalLayout.addItem(horizontalSpacer)
		horizontalLayout.addWidget(pushButton)

		verticalLayout_2.addWidget(self.lb_taskName)
		verticalLayout_2.addLayout(horizontalLayout)

		horizontalLayout_2.addWidget(self.lb_taskThumb)
		horizontalLayout_2.addLayout(verticalLayout_2)

		verticalLayout_3.addWidget(label_2)
		verticalLayout_3.addLayout(horizontalLayout_2)

		horizontalLayout_6 = QHBoxLayout()
		horizontalLayout_6.setSpacing(0)
		horizontalLayout_6.setContentsMargins(0, 0, 0, 0)

		verticalLayout_7 = QVBoxLayout()
		verticalLayout_7.setSpacing(0)
		verticalLayout_7.setContentsMargins(0, 0, 0, 0)

		frame_3 = QFrame(self)
		frame_3.setFrameShape(QFrame.StyledPanel)
		frame_3.setFrameShadow(QFrame.Raised)
		frame_3.setObjectName("publishFile")
		frame_3.setFixedWidth(400)

		verticalLayout_4 = QVBoxLayout(frame_3)
		verticalLayout_4.setSpacing(10)
		verticalLayout_4.setContentsMargins(20, 10, 20, 20)

		label_6 = QLabel("FILE", frame_3)

		horizontalLayout_8 = QHBoxLayout()
		horizontalLayout_8.setSpacing(10)
		horizontalLayout_8.setContentsMargins(0, 0, 0, 0)

		self.cb_taskFile = QComboBox(frame_3)
		self.cb_taskFile.setObjectName("filename")
		self.cb_taskFile.setEditable(True)

		view = QListView(self.cb_taskFile)
		self.cb_taskFile.setView(view)

		self.cb_taskFile.currentIndexChanged.connect(self.update_savename)
		self.cb_taskFile.lineEdit().editingFinished.connect(self.update_savename)
		self.cb_taskFile.lineEdit().setReadOnly(True)

		self.le_taskFile = QLineEdit(frame_3)
		self.le_taskFile.setObjectName("filename")
		self.le_taskFile.setReadOnly(True)
		self.le_taskFile.setMaximumWidth(80)

		horizontalLayout_8.addWidget(self.cb_taskFile)
		horizontalLayout_8.addWidget(self.le_taskFile)

		verticalLayout_4.addWidget(label_6)
		verticalLayout_4.addLayout(horizontalLayout_8)
		verticalLayout_4.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

		frame_6 = QFrame(self)
		frame_6.setFrameShape(QFrame.StyledPanel)
		frame_6.setFrameShadow(QFrame.Raised)
		frame_6.setObjectName("publishThumb")
		frame_6.setFixedWidth(400)
		frame_6.setFixedHeight(200)

		verticalLayout_6 = QVBoxLayout(frame_6)
		verticalLayout_6.setSpacing(0)
		verticalLayout_6.setContentsMargins(0, 0, 0, 0)

		self.lb_screen = QLabel(frame_6)

		verticalLayout_6.addWidget(self.lb_screen)

		pushButton_4 = QPushButton("Refresh", frame_6)
		pushButton_4.move(300, 20)
		pushButton_4.setObjectName("smallDark")
		pushButton_4.setFixedHeight(20)
		pushButton_4.setFixedWidth(80)
		pushButton_4.clicked.connect(self.screenTake)

		verticalLayout_7.addWidget(frame_3)
		verticalLayout_7.addWidget(frame_6)

		frame_4 = QFrame(self)
		frame_4.setFrameShape(QFrame.StyledPanel)
		frame_4.setFrameShadow(QFrame.Raised)
		frame_4.setObjectName("publishText")

		verticalLayout_5 = QVBoxLayout(frame_4)
		verticalLayout_5.setSpacing(10)
		verticalLayout_5.setContentsMargins(20, 10, 20, 20)

		label_8 = QLabel("REPORT TEXT", frame_4)

		self.te_report = QTextEdit(frame_4)
		self.te_report.setObjectName("report")
		self.te_report.setAcceptRichText(False)
		self.te_report.document().setDocumentMargin(0)

		if capp.QT5:
			self.te_report.setPlaceholderText("Type here...")

		horizontalLayout_7 = QHBoxLayout()
		horizontalLayout_7.setSpacing(10)
		horizontalLayout_7.setContentsMargins(0, 0, 0, 0)

		lb_addfile = QLabel("Add file:", frame_4)
		lb_addfile.setFixedWidth(50)

		pb_link = QPushButton("As link", frame_4)
		pb_link.clicked.connect(lambda: self.add_files(True))
		pb_link.setObjectName("small")

		pb_upload = QPushButton("As attachment", frame_4)
		pb_upload.clicked.connect(lambda: self.add_files(False))
		pb_upload.setObjectName("small")

		horizontalLayout_7.addWidget(lb_addfile)
		horizontalLayout_7.addWidget(pb_link)
		horizontalLayout_7.addWidget(pb_upload)
		horizontalLayout_7.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

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

		horizontalLayout_3 = QHBoxLayout()
		horizontalLayout_3.setSpacing(10)
		horizontalLayout_3.setContentsMargins(0, 0, 0, 0)

		label_9 = QLabel("Status:", frame_4)
		label_9.setFixedWidth(50)

		self.cb_status = QComboBox(self)
		view = QListView(self.cb_status)
		self.cb_status.setView(view)

		horizontalSpacer_3 = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

		horizontalLayout_3.addWidget(label_9)
		horizontalLayout_3.addWidget(self.cb_status)
		horizontalLayout_3.addItem(horizontalSpacer_3)

		horizontalLayout_4 = QHBoxLayout()
		horizontalLayout_4.setSpacing(10)
		horizontalLayout_4.setContentsMargins(0, 0, 0, 0)

		label_10 = QLabel("Hours:", frame_4)
		label_10.setFixedWidth(50)

		self.cb_time = QComboBox(self)
		view = QListView(self.cb_time)
		self.cb_time.setView(view)

		hours = ["{0}h {1}m".format(i, j if j == 0 else 30) for i in range(13) for j in range(2)][1:-1]

		self.cb_time.addItems(hours)
		self.cb_time.setEditable(True)
		self.cb_time.lineEdit().setInputMask("00\h 00\m")

		horizontalSpacer_2 = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

		horizontalLayout_4.addWidget(label_10)
		horizontalLayout_4.addWidget(self.cb_time)
		horizontalLayout_4.addItem(horizontalSpacer_2)

		verticalLayout_5.addWidget(label_8)
		verticalLayout_5.addWidget(self.te_report)
		verticalLayout_5.addWidget(self.tableWidget)
		verticalLayout_5.addLayout(horizontalLayout_7)
		verticalLayout_5.addLayout(horizontalLayout_3)
		verticalLayout_5.addLayout(horizontalLayout_4)

		horizontalLayout_6.addLayout(verticalLayout_7)
		horizontalLayout_6.addWidget(frame_4)

		frame_5 = QFrame(self)
		frame_5.setFrameShape(QFrame.StyledPanel)
		frame_5.setFrameShadow(QFrame.Raised)
		frame_5.setObjectName("publishButtons")
		frame_5.setFixedHeight(48)

		horizontalLayout_5 = QHBoxLayout(frame_5)
		horizontalLayout_5.setSpacing(20)
		horizontalLayout_5.setContentsMargins(20, 10, 20, 10)

		horizontalSpacer_4 = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

		self.pb_publish = QPushButton("Publish", frame_5)
		self.pb_publish.clicked.connect(self.sendReport)

		self.pb_cancel = QPushButton("Cancel", frame_5)
		self.pb_cancel.clicked.connect(self.stop)
		self.pb_cancel.setObjectName("dark")

		horizontalLayout_5.addItem(horizontalSpacer_4)
		horizontalLayout_5.addWidget(self.pb_publish)
		horizontalLayout_5.addWidget(self.pb_cancel)

		verticalLayout_8.addWidget(frame)
		verticalLayout_8.addWidget(frame_2)
		verticalLayout_8.addLayout(horizontalLayout_6)
		verticalLayout_8.addWidget(frame_5)

		self.setLayout(verticalLayout_8)

	def run(self):
		self.show()

	def stop(self):
		self.close()

	def closeEvent(self, event):
		self.close()

