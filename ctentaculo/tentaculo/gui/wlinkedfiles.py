# -*- coding: utf-8 -*-
import sys, os, time, datetime

from tentaculo.core import capp, config, fmanager, utils
from tentaculo.gui import style
from tentaculo.gui.elements import filelist
from tentaculo.api.icerebro import db

from tentaculo.Qt.QtGui import *
from tentaculo.Qt.QtCore import *
from tentaculo.Qt.QtWidgets import *
from tentaculo.Qt import QtCompat


class w_linkedfiles(QDialog):
	NAME = 'LINKED_WINDOW'
	TITLE = 'Select file to start working on'
	parent = None

	__task = None
	__selected_task_id = None
	__selected_file_id = None
	__selected_file_path = None

	__filter_mode = 0

	def __init__(self, parent = None):
		super(self.__class__, self).__init__(parent = parent)
		self.initData()
		self.initUI()
		self.initStyle()

	def initData(self):
		self.conn = db.Db()
		self.fman = fmanager.FManager()
		self.config = config.Config()

	def initStyle(self):
		styler = style.Styler()
		styler.initStyle(self)

	def initUI(self):
		self.setObjectName(self.NAME)
		self.setWindowTitle(self.TITLE)
		self.setObjectName("ABOUT_WINDOW")
		self.setMinimumSize(400, 500)
		self.setMaximumWidth(400)

		verticalLayout = QVBoxLayout(self)
		verticalLayout.setContentsMargins(0, 0, 0, 0)
		verticalLayout.setSpacing(10)

		verticalLayout_2 = QVBoxLayout()
		verticalLayout_2.setContentsMargins(10, 10, 10, 10)
		verticalLayout_2.setSpacing(10)

		horizontalLayout_2 = QHBoxLayout()
		horizontalLayout_2.setContentsMargins(10, 0, 10, 0)
		horizontalLayout_2.setSpacing(10)

		label = QLabel("FILES", self)

		horizontalSpacer_2 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

		self.pb_filterVersions = QPushButton("Show Recent Versions", self)
		self.pb_filterVersions.setObjectName("flat")
		self.pb_filterVersions.clicked.connect(self.filter_toggle)

		horizontalLayout_2.addWidget(label)
		horizontalLayout_2.addItem(horizontalSpacer_2)
		horizontalLayout_2.addWidget(self.pb_filterVersions)

		self.tableWidget = QTableWidget(self)
		self.tableWidget.setObjectName("files")
		self.tableWidget.setColumnCount(2)
		self.tableWidget.setColumnHidden(1, True)
		self.tableWidget.setColumnWidth(0, 300)
		self.tableWidget.setSortingEnabled(True)
		self.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
		QtCompat.setSectionResizeMode(self.tableWidget.verticalHeader(), QHeaderView.ResizeToContents)
		self.tableWidget.verticalHeader().setDefaultSectionSize(20)		
		self.tableWidget.verticalHeader().hide()
		QtCompat.setSectionResizeMode(self.tableWidget.horizontalHeader(), QHeaderView.ResizeToContents)
		self.tableWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.tableWidget.horizontalHeader().setSortIndicator(0, Qt.DescendingOrder)
		self.tableWidget.horizontalHeader().hide()
		self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
		self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
		self.tableWidget.setShowGrid(False)
		self.tableWidget.setAlternatingRowColors(True)
		#self.tableWidget.customContextMenuRequested.connect(self.__popupAt)
		self.tableWidget.currentCellChanged.connect(self.__cellChanged)
		#self.tableWidget.cellDoubleClicked.connect(self.__cellActivated)

		horizontalLayout = QHBoxLayout()
		horizontalLayout.setContentsMargins(0, 0, 0, 0)
		horizontalLayout.setSpacing(10)

		self.pb_taskStart = QPushButton("Start working on this file", self)
		self.pb_taskStart.clicked.connect(lambda: self.startTask())
		self.pb_taskStart.setEnabled(False)

		horizontalSpacer = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

		horizontalLayout.addWidget(self.pb_taskStart)
		horizontalLayout.addItem(horizontalSpacer)

		self.taskThumb = QLabel(self)
		self.taskThumb.setFixedSize(400, 200)
		self.taskThumb.setObjectName("tasksThumb")
		self.taskThumb.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
		self.__set_image()

		verticalLayout_2.addLayout(horizontalLayout_2)
		verticalLayout_2.addWidget(self.tableWidget)
		verticalLayout_2.addLayout(horizontalLayout)

		verticalLayout.addLayout(verticalLayout_2)
		verticalLayout.addWidget(self.taskThumb)	
		
	def sort(self):
		self.tableWidget.sortItems(1, Qt.DescendingOrder)

	def filter_toggle(self):
		self.__filter_mode += 1
		if self.__filter_mode > 2:
			self.__filter_mode = 0

		self.filter(self.__filter_mode)
		
	# 0 - Show all
	# 1 - Show recent
	# 2 - Hide versions
	def filter(self, mode = 0):
		self.__filter_mode = mode
		if self.__filter_mode == 0:
			self.pb_filterVersions.setText("Show Recent Versions")

			for i in range(self.tableWidget.rowCount()):
				fitem = self.tableWidget.item(i, 1)
				self.tableWidget.setRowHidden(i, fitem.is_local)
		elif self.__filter_mode == 1:
			self.pb_filterVersions.setText("Hide Versions")

			for i in range(self.tableWidget.rowCount()):
				fitem = self.tableWidget.item(i, 1)
				self.tableWidget.setRowHidden(i, not fitem.is_publish and not fitem.is_local and not fitem.is_last)
		elif self.__filter_mode == 2:
			self.pb_filterVersions.setText("Show All Versions")

			for i in range(self.tableWidget.rowCount()):
				fitem = self.tableWidget.item(i, 1)
				self.tableWidget.setRowHidden(i, not fitem.is_publish)

	def startTask(self):
		if self.__selected_task_id is None: return None
		started = False

		if self.__selected_file_path is None or self.__selected_file_id is None:
			fvers = vfile.VFile(self.config.translate(self.__task))
			has_local = os.path.exists(fvers.local_path())
			if fvers.has_versions or has_local:
				file_path = None
				local_ver = self.config.version_for_file(fvers.local_path())
				if has_local and ((local_ver and local_ver >= fvers.last_number) or not fvers.has_versions):
					file_path = fvers.local_path()
				else:
					file_path = os.path.join(fvers.path_version, fvers.versions[fvers.last_number])

				if self.fman.open(self.__task, file_path, True):
					self.conn.set_work_status(self.__selected_task_id)
					started = True
			else:
				if self.fman.create(self.__task):
					self.conn.set_work_status(self.__selected_task_id)
					started = True
		else:
			if self.fman.open(self.__task, self.__selected_file_path, True):
				self.conn.set_work_status(self.__selected_task_id)
				started = True

		self.done(1 if started else -1)
				
	def clearTask(self):
		self.__task = None
		self.__selected_task_id = None
		self.__selected_file_id = None
		self.__selected_file_path = None
		self.pb_taskStart.setEnabled(False)
		self.__set_image()
		self.tableWidget.clear()
		self.tableWidget.setRowCount(0)
		
	def setTask(self, task = None):
		self.clearTask()

		if task is not None:
			self.__task = task
			self.__selected_task_id = task["id"]
			self.update_table()

	def update_table(self):
		if self.__task is not None:
			valid = self.config.task_valid(self.__task)
			taskFiles = []
			linked = self.conn.linked_tasks(self.__selected_task_id)
			if linked is not None:
				for t in linked:
					taskFiles += self.conn.task_files(t).values()

			self.tableWidget.setSortingEnabled(False)
			self.tableWidget.setRowCount(len(taskFiles))

			for i, file in enumerate(taskFiles):
				self.tableWidget.setCellWidget(i, 0, filelist.makeFileWidget(file))
				self.tableWidget.setItem(i, 1, filelist.FileItem(file))

			self.tableWidget.setColumnHidden(1, True)
			self.tableWidget.setSortingEnabled(True)
			self.sort()
			self.filter(self.__filter_mode)
			self.tableWidget.setCurrentCell(-1, -1) 

	def __set_image(self, thumb = None):
		logo = QImage(utils.getResDir("image.png")) if thumb is None else QImage(thumb).scaled(400, 200, Qt.KeepAspectRatioByExpanding)

		if logo.isNull():
			logo = QImage(utils.getResDir("image.png"))

		self.taskThumb.setPixmap(QPixmap.fromImage(logo))

	def __cellChanged(self, newRow, newCol, lastRow = 0, lastCol = 0):
		fitem = self.tableWidget.item(newRow, 1)

		if fitem is not None:
			self.pb_taskStart.setEnabled(True)
			self.__set_image(fitem.thumbnail)

			self.__selected_file_path = fitem.path
			self.__selected_file_id = fitem.id

	def run(self):
		self.activateWindow()
		return self.exec_()

	def stop(self):
		self.done(-1)

