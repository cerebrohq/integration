# -*- coding: utf-8 -*-
import sys, os, time, shutil, inspect

from tentaculo.core import capp, jsonio, config, clogger
from tentaculo.api.icerebro import db
from tentaculo.gui import style
from tentaculo.gui.elements import tasklist, filelist, taskheader, taskcontrols, taskdefinition

from tentaculo.Qt.QtGui import *
from tentaculo.Qt.QtCore import *
from tentaculo.Qt.QtWidgets import *

class w_taskwindow(QWidget):
	task_set = Signal()

	NAME = "TASK_WINDOW"
	parent = None
	conn = None
	state_file = "ui_taskwindow.json"
	selected_task = None

	def __init__(self, task_select = False, link_mode = False, parent = None):
		capp.clearUI(self.NAME)
		super(self.__class__, self).__init__(parent = parent)
		self.conn = db.Db()
		self.log = clogger.CLogger().log
		self.config = None
		self.initStyle()
		uname = u"" if not self.conn.connected else u" : {0}".format(self.conn.user_name)
		if task_select:
			self.TITLE = u"Select task" + uname
		else:
			self.TITLE = u"Link/Embed" + uname if link_mode else u"Todo list" + uname
		self.initUI(task_select, link_mode)
		self.initData()
		self.refresh_tasks()
		self.load_state()

	def event(self, event):
		if event.type() == QEvent.WindowDeactivate:
			capp.focus_out()
		elif event.type() == QEvent.WindowActivate:
			capp.focus_in()
		return super(self.__class__, self).event(event)

	def initStyle(self):
		styler = style.Styler()
		styler.initStyle(self)

	def initData(self):
		if not self.conn.connected:
			self.conn.autologin()
		if self.conn.connected:
			self.config = config.Config()

	def save_state(self):
		state = {}
		geometry = self.geometry()
		state["tab"] = self.tabWidget.currentIndex()
		state["tasklist"] = self.taskList.sort_column()
		state["tasklist_id"] = self.taskList.task_id
		state["browselist"] = self.browseList.sort_column()
		state["browselist_id"] = self.browseList.task_id
		state["taskfiles"] = self.taskFiles.filter_mode()
		state["browsefiles"] = self.browseFiles.filter_mode()
		state["window"] = [geometry.x(), geometry.y(), geometry.width(), geometry.height()]
		jsonio.write(os.path.join(capp.configdir(), self.state_file), state)

	def load_state(self):
		state = jsonio.read(os.path.join(capp.configdir(), self.state_file))
		if state is not None and len(state) > 0:
			self.tabWidget.setCurrentIndex(state["tab"])

			self.cb_taskSort.setCurrentIndex(state["tasklist"][0])

			self.taskList.setSortColumn(state["tasklist"][0])
			self.taskList.setSortColumn(state["tasklist"][0], True if state["tasklist"][1] == Qt.DescendingOrder else False)
			self.tasklist_select(state["tasklist_id"])
			self.taskFiles.filter(state["taskfiles"])

			task = self.conn.task(state["browselist_id"])
			if task is not None:
				self.browselist_parent(task["parent"])
			self.browselist_select(state["browselist_id"])
			self.browseFiles.filter(state["browsefiles"])
			geometry = state["window"]
			if geometry is not None and len(geometry) == 4:
				self.setGeometry(geometry[0], geometry[1], geometry[2], geometry[3])

	def tasklist_clear(self):
		self.taskFiles.clearTask()
		self.taskHeader.clearTask()
		self.taskDefinition.clearTask()
		self.taskControls.clearTask()

	def tasklist_select(self, task_id):
		if self.taskList.select_task(task_id):
			self.tasklist_set(self.conn.task(task_id))
		else:
			self.tasklist_clear()

	def tasklist_set(self, task):
		if task is not None and task["id"] == self.taskList.task_id:
			self.conn.task_files(self.taskList.task_id)

			self.taskFiles.setTask(task)
			self.taskHeader.setTask(task)
			self.taskDefinition.setTask(task)
			self.taskControls.setTask(task)
		else:
			self.tasklist_clear()

	def tasklist_refresh(self):
		self.tasklist_clear()
		tasks = self.conn.allocated_tasks()
		self.taskList.setTasks(tasks)

	def tasklist_sort(self, index):
		self.taskList.setSortColumn(index, True)

	def browselist_clear(self):
		self.browseFiles.clearTask()
		self.browseHeader.clearTask()
		self.browseDefinition.clearTask()
		self.browseControls.clearTask()
		self.le_search.clear()

	def browselist_select(self, task_id):
		if self.browseList.select_task(task_id):
			self.browselist_set(self.conn.task(task_id))
		else:
			self.browselist_clear()

	def browselist_set(self, task):
		if task is not None and task["id"] == self.browseList.task_id:
			self.conn.task_files(self.browseList.task_id)

			self.browseFiles.setTask(task)
			self.browseHeader.setTask(task)
			self.browseDefinition.setTask(task)
			self.browseControls.setTask(task)
		else:
			self.browselist_clear()

	def browselist_refresh(self):
		self.browselist_clear()
		tasks = self.conn.tasks()
		self.browseList.setTasks(tasks)

		self.pb_browseUp.setVisible(self.conn.current_parent != 0)
		self.lb_browsePath.setText(self.conn.current_path())

	def browselist_parent(self, task_id = None):
		self.conn.set_parent(task_id)
		self.browselist_refresh()

	def refresh_tasks(self):
		#self.conn.refresh()

		self.tasklist_refresh()
		self.browselist_refresh()

	def refresh_task(self, task_id):
		task = self.conn.refresh_task(task_id)

		self.taskList.set_task(task)
		self.tasklist_set(task)
		self.browseList.set_task(task)
		self.browselist_set(task)

	def report_task(self, task_id, to_publish = False):
		if task_id is not None:			
			from tentaculo.gui import sendreport
			wndParent = capp.app_window()
			wnd = sendreport.w_createReport(task_id, to_publish, wndParent)
			wnd.run()

			self.stop()

	def select_task(self, task_id):
		if task_id is not None:
			self.selected_task = task_id
			self.task_set.emit()
			self.stop()

	def initUI(self, task_select = False, link_mode = False):
		#window init start
		self.setWindowFlags(Qt.Window)
		self.setObjectName(self.NAME)
		self.setWindowTitle(self.TITLE)
		self.setMinimumSize(1100, 600)
		self.resize(1200, 700)
		self.setContentsMargins(0, 0, 0, 0)
		#window init end

		verticalLayout_9 = QVBoxLayout(self)
		verticalLayout_9.setContentsMargins(0, 0, 0, 0)
		verticalLayout_9.setSpacing(0)
		self.tabWidget = QTabWidget(self)

		# TAB My tasks
		tab = QWidget();
		horizontalLayout_6 = QHBoxLayout(tab);
		horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
		horizontalLayout_6.setSpacing(0)

		verticalLayout_2 = QVBoxLayout()
		verticalLayout_2.setContentsMargins(0, 0, 0, 0)
		verticalLayout_2.setSpacing(0)

		# TASKS SORT
		frame = QFrame(tab);
		frame.setFrameShape(QFrame.StyledPanel)
		frame.setFrameShadow(QFrame.Raised);
		frame.setObjectName("tasksSort")
		frame.setFixedWidth(400)

		horizontalLayout = QHBoxLayout(frame);
		horizontalLayout.setContentsMargins(20, 0, 15, 0)
		horizontalLayout.setSpacing(10)

		label = QLabel("Sort by:", frame)

		self.cb_taskSort = QComboBox(self)
		view = QListView(self.cb_taskSort)
		self.cb_taskSort.setView(view)
		self.cb_taskSort.addItem("Task Name")
		self.cb_taskSort.addItem("Status")
		self.cb_taskSort.addItem("Activity")
		self.cb_taskSort.addItem("Deadline")
		self.cb_taskSort.activated.connect(self.tasklist_sort)

		self.toolButton = QToolButton(frame)
		self.toolButton.setObjectName("settings")
		self.toolButton.setPopupMode(QToolButton.InstantPopup)

		self.toolMenu = QMenu(self.toolButton)
		#self.toolMenu.addAction("1 Test action")
		#self.toolMenu.addAction("2 Test action")

		self.toolButton.setMenu(self.toolMenu)

		horizontalSpacer_9 = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

		horizontalLayout.addWidget(label)
		horizontalLayout.addWidget(self.cb_taskSort)
		horizontalLayout.addItem(horizontalSpacer_9)
		horizontalLayout.addWidget(self.toolButton)

		# TASKS LIST
		self.taskList = tasklist.TaskList(False, tab)
		self.taskList.clicked.connect(lambda: self.tasklist_select(self.taskList.task_id))

		verticalLayout_2.addWidget(frame)
		verticalLayout_2.addWidget(self.taskList)

		verticalLayout_8 = QVBoxLayout();
		verticalLayout_8.setContentsMargins(0, 0, 0, 0)
		verticalLayout_8.setSpacing(0)

		# TASKS HEADER
		self.taskHeader = taskheader.TaskHeader(tab)

		horizontalLayout_4 = QHBoxLayout()
		horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
		horizontalLayout_4.setSpacing(0)

		# TASKS FILES
		self.taskFiles = filelist.FileList(task_select = task_select, link_mode = link_mode, parent = tab)
		self.taskFiles.refresh.connect(lambda: self.refresh_task(self.taskList.task_id))
		self.taskFiles.request_close.connect(self.stop)
		
		# TASKS DEFINITION
		self.taskDefinition = taskdefinition.TaskDefinition(tab)

		horizontalLayout_4.addWidget(self.taskFiles)
		horizontalLayout_4.addWidget(self.taskDefinition)

		# TASKS BUTTONS
		self.taskControls = taskcontrols.TaskControls(task_select, tab)
		self.taskControls.setVisible(not link_mode)
		self.taskControls.publish.connect(lambda to_publish: self.select_task(self.taskList.task_id) if task_select else self.report_task(self.taskList.task_id, to_publish))

		# TASKS GLOBAL
		verticalLayout_8.addWidget(self.taskHeader)
		verticalLayout_8.addLayout(horizontalLayout_4)
		verticalLayout_8.addWidget(self.taskControls)

		horizontalLayout_6.addLayout(verticalLayout_2)
		horizontalLayout_6.addLayout(verticalLayout_8)

		self.tabWidget.addTab(tab, "Todo list")

		# TAB Projects browser
		tab_2 = QWidget()

		horizontalLayout_14 = QHBoxLayout(tab_2)
		horizontalLayout_14.setContentsMargins(0, 0, 0, 0)
		horizontalLayout_14.setSpacing(0)

		verticalLayout_17 = QVBoxLayout()
		verticalLayout_17.setContentsMargins(0, 0, 0, 0)
		verticalLayout_17.setSpacing(0)

		# BROWSE SEARCH
		frame_8 = QFrame(tab_2)
		frame_8.setFrameShape(QFrame.StyledPanel)
		frame_8.setFrameShadow(QFrame.Raised)
		frame_8.setObjectName("browseSearch")
		frame_8.setFixedWidth(400)

		horizontalLayout_13 = QHBoxLayout(frame_8)
		horizontalLayout_13.setContentsMargins(20, 0, 15, 0)
		horizontalLayout_13.setSpacing(0)

		frame_17 = QFrame(frame_8)
		frame_17.setFrameShape(QFrame.StyledPanel)
		frame_17.setFrameShadow(QFrame.Raised)
		frame_17.setObjectName("searchBar")
		frame_17.setFixedSize(250, 26)

		horizontalLayout_15 = QHBoxLayout(frame_17)
		horizontalLayout_15.setContentsMargins(5, 0, 0, 0)
		horizontalLayout_15.setSpacing(0)

		searchIcon = QLabel(frame_17)
		iconfile = capp.getResDir("search.png")
		searchIcon.setPixmap(QPixmap(iconfile))
		searchIcon.setFixedSize(26, 26)
		searchIcon.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

		self.le_search = QLineEdit(frame_17)
		self.le_search.setObjectName("search")
		self.le_search.setPlaceholderText("Search...")

		horizontalLayout_15.addWidget(searchIcon)
		horizontalLayout_15.addWidget(self.le_search)

		horizontalSpacer_6 = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

		# BROWSE FILTER SETTINGS
		self.toolButton_2 = QToolButton(frame_8)
		self.toolButton_2.setObjectName("settings")
		self.toolButton_2.setPopupMode(QToolButton.InstantPopup)

		self.toolMenu_2 = QMenu(self.toolButton_2)
		#self.toolMenu_2.addAction("1 Test action")
		#self.toolMenu_2.addAction("2 Test action")

		self.toolButton_2.setMenu(self.toolMenu_2)

		horizontalLayout_13.addWidget(frame_17)
		horizontalLayout_13.addItem(horizontalSpacer_6)
		horizontalLayout_13.addWidget(self.toolButton_2)

		# BROWSE PATH
		frame_9 = QFrame(tab_2)
		frame_9.setFrameShape(QFrame.StyledPanel)
		frame_9.setFrameShadow(QFrame.Raised)
		frame_9.setObjectName("browsePath")
		frame_9.setFixedWidth(400)

		horizontalLayout_12 = QHBoxLayout(frame_9)
		horizontalLayout_12.setContentsMargins(20, 0, 20, 0)
		horizontalLayout_12.setSpacing(0)

		self.lb_browsePath = QLabel("/", frame_9)
		self.lb_browsePath.setObjectName("active")

		horizontalLayout_12.addWidget(self.lb_browsePath)

		verticalLayout_16 = QVBoxLayout(tab_2)
		verticalLayout_16.setContentsMargins(0, 0, 0, 0)
		verticalLayout_16.setSpacing(0)

		# BROWSE UP BUTTON
		self.pb_browseUp = QPushButton("Back", tab_2)
		self.pb_browseUp.setFixedSize(400, 80)
		self.pb_browseUp.setObjectName("browseUp")
		self.pb_browseUp.setIcon(QIcon(capp.getResDir("nav-back.png")))
		self.pb_browseUp.setIconSize(QSize(47, 46))
		self.pb_browseUp.setVisible(False)
		self.pb_browseUp.clicked.connect(lambda: self.browselist_parent())

		# BROWSE LIST
		self.browseList = tasklist.TaskList(True, tab_2)
		self.browseList.clicked.connect(lambda: self.browselist_select(self.browseList.task_id))
		self.browseList.doubleClicked.connect(lambda: self.browselist_parent(self.browseList.task_id))
		self.le_search.textChanged.connect(self.browseList.setFilter)

		verticalLayout_17.addWidget(frame_8)
		verticalLayout_17.addWidget(frame_9)
		verticalLayout_17.addWidget(self.pb_browseUp)
		verticalLayout_17.addWidget(self.browseList)

		verticalLayout_15 = QVBoxLayout()
		verticalLayout_15.setContentsMargins(0, 0, 0, 0)
		verticalLayout_15.setSpacing(0)

		# BROWSE HEADER
		self.browseHeader = taskheader.TaskHeader(tab_2)

		horizontalLayout_10 = QHBoxLayout()
		horizontalLayout_10.setContentsMargins(0, 0, 0, 0)
		horizontalLayout_10.setSpacing(0)

		# BROWSE FILES
		self.browseFiles = filelist.FileList(task_select = task_select, link_mode = link_mode, parent = tab_2)
		self.browseFiles.refresh.connect(lambda: self.refresh_task(self.browseList.task_id))
		self.browseFiles.request_close.connect(self.stop)

		# BROWSE DEFINITION
		self.browseDefinition = taskdefinition.TaskDefinition(tab_2)

		horizontalLayout_10.addWidget(self.browseFiles)
		horizontalLayout_10.addWidget(self.browseDefinition)

		# BROWSE BUTTONS
		self.browseControls = taskcontrols.TaskControls(task_select, tab_2)
		self.browseControls.setVisible(not link_mode)
		self.browseControls.publish.connect(lambda to_publish: self.select_task(self.browseList.task_id) if task_select else self.report_task(self.browseList.task_id, to_publish))

		verticalLayout_15.addWidget(self.browseHeader)
		verticalLayout_15.addLayout(horizontalLayout_10)
		verticalLayout_15.addWidget(self.browseControls)

		horizontalLayout_14.addLayout(verticalLayout_17)
		horizontalLayout_14.addLayout(verticalLayout_15)

		self.tabWidget.addTab(tab_2, "Browser")

		verticalLayout_9.addWidget(self.tabWidget)

		self.tabWidget.setCurrentIndex(1 if task_select or link_mode else 0)

	def run(self):
		self.show()

	def stop(self):
		self.save_state()
		self.close()

	def closeEvent(self, event):
		self.save_state()
		self.close()
