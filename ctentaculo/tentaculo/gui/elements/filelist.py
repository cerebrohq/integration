# -*- coding: utf-8 -*-
import os, datetime
from tentaculo.gui import style

from tentaculo.core import capp, fmanager, config, clogger, vfile, utils
from tentaculo.api.icerebro import db

from tentaculo.Qt.QtGui import *
from tentaculo.Qt.QtCore import *
from tentaculo.Qt.QtWidgets import *
from tentaculo.Qt import QtCompat


class FileList(QFrame):
	refresh = Signal()
	request_close = Signal()

	def __init__(self, link_mode = False, task_select = False, parent = None):
		super(self.__class__, self).__init__(parent = parent)
		self.initData(link_mode, task_select)
		self.initUI()
		self.initStyle()

	def initData(self, link_mode = False, task_select = False):
		self.log = clogger.CLogger().log
		self.conn = db.Db()
		self.config = config.Config()
		self.fman = fmanager.FManager()

		self.__task = None
		self.__selected_task_id = None
		self.__selected_file_id = None
		self.__selected_file_path = None
		self.__selected_file_task = None

		self.__task_enabled = False
		self.__filter_mode = 0

		self.__link_mode = link_mode
		self.__task_select = task_select

	def initStyle(self):
		styler = style.Styler()
		styler.initStyle(self)

	def initUI(self):
		self.setFrameShape(QFrame.StyledPanel)
		self.setFrameShadow(QFrame.Raised)
		self.setObjectName("tasksFiles")
		self.setFixedWidth(400)

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
		self.tableWidget.customContextMenuRequested.connect(self.__popupAt)
		self.tableWidget.currentCellChanged.connect(self.__cellChanged)
		#self.tableWidget.cellDoubleClicked.connect(self.__cellActivated)

		horizontalLayout = QHBoxLayout()
		horizontalLayout.setContentsMargins(0, 0, 0, 0)
		horizontalLayout.setSpacing(10)

		self.pb_taskStart = QPushButton("Start working on this task", self)
		self.pb_taskStart.clicked.connect(lambda: self.startTask())
		self.pb_taskStart.setVisible(not self.__link_mode and not self.__task_select)
		self.pb_taskStart.setEnabled(False)

		self.fileButton = QToolButton(self)
		self.fileButton.setObjectName("more")
		self.fileButton.setPopupMode(QToolButton.InstantPopup)

		self.fileMenu = QMenu(self.fileButton)
		act = self.fileMenu.addAction("New File")
		act.triggered.connect(self.newFile)
		act = self.fileMenu.addAction("Import from Preceeding Task")
		act.triggered.connect(lambda: self.select_linked())

		self.fileButton.setMenu(self.fileMenu)
		self.fileButton.setVisible(not self.__link_mode and not self.__task_select)
		self.fileButton.setEnabled(False)

		self.pb_link = QPushButton("Link", self)
		self.pb_link.setVisible(self.__link_mode and not self.__task_select)
		self.pb_link.setEnabled(False)
		self.pb_link.clicked.connect(lambda: self.importSelectedFile(True))

		self.pb_embed = QPushButton("Embed", self)
		self.pb_embed.setVisible(self.__link_mode and not self.__task_select)
		self.pb_embed.setEnabled(False)
		self.pb_embed.clicked.connect(lambda: self.importSelectedFile(False))

		self.pb_open = QPushButton("Open", self)
		self.pb_open.setVisible(self.__link_mode and not self.__task_select)
		self.pb_open.setEnabled(False)
		self.pb_open.clicked.connect(self.openSelectedFile)

		horizontalSpacer = QSpacerItem(5, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

		horizontalLayout.addWidget(self.pb_taskStart)
		horizontalLayout.addWidget(self.fileButton)
		horizontalLayout.addWidget(self.pb_link)
		horizontalLayout.addWidget(self.pb_embed)
		horizontalLayout.addWidget(self.pb_open)
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
				self.tableWidget.setRowHidden(i, self.__link_mode and fitem.is_local)
		elif self.__filter_mode == 1:
			self.pb_filterVersions.setText("Hide Versions")

			for i in range(self.tableWidget.rowCount()):
				fitem = self.tableWidget.item(i, 1)
				self.tableWidget.setRowHidden(i, not fitem.is_publish and (not fitem.is_local or self.__link_mode) and not fitem.is_last)
		elif self.__filter_mode == 2:
			self.pb_filterVersions.setText("Show All Versions")

			for i in range(self.tableWidget.rowCount()):
				fitem = self.tableWidget.item(i, 1)
				self.tableWidget.setRowHidden(i, not fitem.is_publish)

	def filter_mode(self):
		return self.__filter_mode

	def startTask(self):
		if self.__selected_task_id is None or not self.__task_enabled: return None
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

				if self.fman.open(self.__task, file_path, False):
					self.conn.set_work_status(self.__selected_task_id)
					started = True
			else:
				if self.fman.create(self.__task):
					self.conn.set_work_status(self.__selected_task_id)
					started = True
		else:
			if self.fman.open(self.__task, self.__selected_file_path, False):
				self.conn.set_work_status(self.__selected_task_id)
				started = True

		if started:
			self.refresh.emit()
			self.request_close.emit()

	def newFile(self):
		if self.fman.create(self.__task):
			self.conn.set_work_status(self.__selected_task_id)
			self.refresh.emit()
			self.request_close.emit()

	def openSelectedFile(self):
		if self.__selected_file_path is None or self.__selected_file_id is None:
			return False

		self.fman.view(self.__task, self.__selected_file_path)

	def importSelectedFile(self, as_reference = False):
		if self.__selected_file_path is None or self.__selected_file_id is None or self.__selected_file_task is None:
			return False

		return self.fman.link(self.__selected_file_task, self.__selected_file_path) if as_reference else self.fman.embed(self.__selected_file_task, self.__selected_file_path)

	def clearTask(self):
		self.__task = None
		self.__selected_task_id = None
		self.__selected_file_id = None
		self.__selected_file_task = None
		self.__selected_file_path = None
		self.__task_enabled = False
		self.pb_embed.setEnabled(False)
		self.pb_open.setEnabled(False)
		self.pb_link.setEnabled(False)
		self.pb_taskStart.setEnabled(False)
		self.fileButton.setEnabled(False)
		self.__set_image()
		self.pb_taskStart.setText("Start working on this task")
		self.tableWidget.clear()
		self.tableWidget.setRowCount(0)
		
	def setTask(self, task = None):		
		self.clearTask()

		if task is not None:
			self.__task = task
			self.__selected_task_id = task["id"]
			self.__set_image(task["thumbnail"])
			
			valid = self.config.task_valid(task)
			self.__task_enabled = valid[0] and task["enabled_task"]
			self.log.debug('Task %s is enabled %s', task["path"] + task["name"], self.__task_enabled)
			
			self.pb_taskStart.setEnabled(self.__task_enabled and (not task["name_editable"] or (task.get("files", None) is not None and len(task["files"]) == 0)))
			self.fileButton.setEnabled(self.__task_enabled)
			self.update_table()

	def update_table(self):
		if self.__task is not None:
			valid = self.config.task_valid(self.__task)
			taskFiles = []
			if valid[0]:
				taskFiles = self.__task.get("files", {}).values()
			elif valid[1] and self.__link_mode:
				childTasks = self.conn.children_tasks(self.__selected_task_id)
				if childTasks is not None:
					for t in childTasks:
						taskFiles += self.conn.task_files(t).values()

			self.tableWidget.setSortingEnabled(False)
			self.tableWidget.setRowCount(len(taskFiles))

			for i, file in enumerate(taskFiles):
				self.tableWidget.setCellWidget(i, 0, makeFileWidget(file))
				self.tableWidget.setItem(i, 1, FileItem(file))

			self.tableWidget.setColumnHidden(1, True)
			self.tableWidget.setSortingEnabled(True)
			self.sort()
			self.filter(self.__filter_mode)

	def select_linked(self):
		from tentaculo.gui.wlinkedfiles import w_linkedfiles
		wnd = w_linkedfiles(capp.app_window())
		wnd.setTask(self.__task)
		if (wnd.run() > 0):
			self.refresh.emit()
			self.request_close.emit()

	def __set_image(self, thumb = None):
		logo = QImage(utils.getResDir("image.png")) if thumb is None else QImage(thumb).scaled(400, 200, Qt.KeepAspectRatioByExpanding)

		if logo.isNull():
			logo = QImage(utils.getResDir("image.png"))

		self.taskThumb.setPixmap(QPixmap.fromImage(logo))
	
	def __popupAt(self, pos):
		index = self.tableWidget.indexAt(pos)
		if not index.isValid(): return

		menu = QMenu()
		styler = style.Styler()
		styler.initStyle(menu)

		acts = []
		menu_options = ["Start working on this file", "Open without Starting the Task", None, "Link", "Embed", None, "Show in Explorer", "Copy Local Path to Clipboard"]
		for opt in menu_options:
			if opt is None:
				menu.addSeparator()
			else:
				action = menu.addAction(opt)
				acts.append(action)
		try:
			ind = acts.index(menu.exec_(self.tableWidget.viewport().mapToGlobal(pos)))
			if ind == 0:
				self.startTask()
			elif ind == 1:
				self.openSelectedFile()
			elif ind == 2:
				self.importSelectedFile(True)
			elif ind == 3:
				self.importSelectedFile(False)
			elif ind == 4:
				if self.__selected_file_path is not None:
					utils.show_dir(self.__selected_file_path)
			elif ind == 5:
				if self.__selected_file_path is not None:
					capp.copyToClipboard(self.__selected_file_path)
		except ValueError:
			pass

	def __cellChanged(self, newRow, newCol, lastRow = 0, lastCol = 0):
		fitem = self.tableWidget.item(newRow, 1)

		if fitem is not None:
			self.pb_embed.setEnabled(True)
			self.pb_open.setEnabled(True)
			self.pb_link.setEnabled(True)
			self.pb_taskStart.setText("Start working on this file")
			self.pb_taskStart.setEnabled(self.__task_enabled)
			self.__set_image(fitem.thumbnail)

			self.__selected_file_path = fitem.path
			self.__selected_file_task = fitem.task_id
			self.__selected_file_id = fitem.id

	def __cellActivated(self, row, col):
		fitem = self.tableWidget.item(row, 1)

		if fitem is not None:
			self.__selected_file_path = fitem.path
			self.__selected_file_id = fitem.id
			self.__selected_file_task = fitem.task_id
			self.openSelectedFile()

def makeFileWidget(file):
	wgt = QWidget()

	if file is not None:
		file_id = int(file["id"])
		publish, local, unpublished = file_id == -1, file_id == -2, file_id < -2
		wgt.setFixedSize(380, 30 if publish else 20)

		horizontalLayout = QHBoxLayout(wgt)
		horizontalLayout.setContentsMargins(10, 10 if publish else 0, 10, 0)
		horizontalLayout.setSpacing(0)

		name = file["name"]

		if local and file["version"] is not None:
			name = u"{0} ({1})".format(file["name"], str(file["version"]))

		lb_name = QLabel(name, wgt)
		horizontalSpacer = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

		date = file["date"]
		if date.date() == datetime.date.today():
			date = u"today, {0}".format(date.strftime("%H:%M"))
		else:
			date = date.strftime("%d.%m.%Y")
		lb_date = QLabel(date, wgt)

		lb_icon = QLabel(wgt)
		lb_icon.setFixedSize(20, 20)
		lb_icon.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
		if publish:
			lb_name.setObjectName("publish")
			lb_icon.setPixmap(QPixmap(utils.getResDir("publish.png")))
		elif local or unpublished:
			lb_icon.setPixmap(QPixmap(utils.getResDir("local.png")))

		horizontalLayout.addWidget(lb_name)
		horizontalLayout.addItem(horizontalSpacer)
		horizontalLayout.addWidget(lb_date)
		horizontalLayout.addWidget(lb_icon)

	return wgt

class FileItem(QTableWidgetItem):
	def __init__(self, file):
		super(FileItem, self).__init__()
		self.initData(file)

	def initData(self, file):
		if file is not None:
			self.name = file["name"]
			self.path = file["path"]
			self.id = file["id"]
			self.thumbnail = file["thumbnail"]
			self.task_id = file["task_id"]
			self.is_publish = self.id == -1
			self.is_local = self.id == -2
			self.is_last = file["is_last_version"]

	def __lt__(self, other):
		if self.task_id == other.task_id:
			if self.is_publish or other.is_publish:
				return other.is_publish
			elif self.is_local or other.is_local:
				return other.is_local
			else:
				return self.name < other.name
		else:
			return self.task_id < other.task_id
