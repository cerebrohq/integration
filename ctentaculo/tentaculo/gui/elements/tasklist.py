# -*- coding: utf-8 -*-
import locale, webbrowser
from tentaculo.gui import style, wapp

from tentaculo.core import capp, clogger, config, utils, utils, fmanager
from tentaculo.api.icerebro import db

from tentaculo.Qt.QtGui import *
from tentaculo.Qt.QtCore import *
from tentaculo.Qt.QtWidgets import *
from tentaculo.Qt import QtCompat

COLUMN_COUNT = 6


class TaskList(QFrame):
	refresh = Signal()
	clicked = Signal()
	doubleClicked = Signal()

	task_id = None
	__tree_display = False
	__sort_column = 4

	def __init__(self, treeDisplay = False, parent = None):
		super(self.__class__, self).__init__(parent = parent)
		self.log = clogger.CLogger().log
		self.conn = db.Db()
		self.fman = fmanager.FManager()
		self.config = config.Config()
		self.__tree_display = treeDisplay
		self.initUI()
		self.initStyle()

	def initStyle(self):
		styler = style.Styler()
		styler.initStyle(self)

	def initUI(self):
		self.setFrameShape(QFrame.StyledPanel)
		self.setFrameShadow(QFrame.Raised)
		self.setObjectName("tasksList")
		self.setFixedWidth(400)

		verticalLayout = QVBoxLayout(self)
		verticalLayout.setContentsMargins(0, 0, 0, 0)
		verticalLayout.setSpacing(0)

		self.tableWidget = QTableWidget(self)
		self.tableWidget.setObjectName("tasks")
		self.tableWidget.setColumnCount(COLUMN_COUNT)
		self.tableWidget.setRowCount(0)
		for i in range(1, COLUMN_COUNT):
			self.tableWidget.setColumnHidden(i, True)
		self.tableWidget.setColumnWidth(0, 400)
		self.tableWidget.setSortingEnabled(True)
		self.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
		QtCompat.setSectionResizeMode(self.tableWidget.verticalHeader(), QHeaderView.Fixed)
		self.tableWidget.verticalHeader().setDefaultSectionSize(80)
		self.tableWidget.verticalHeader().hide()
		QtCompat.setSectionResizeMode(self.tableWidget.horizontalHeader(), QHeaderView.ResizeToContents)
		self.tableWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.tableWidget.horizontalHeader().setSortIndicator(0, Qt.AscendingOrder)
		self.tableWidget.horizontalHeader().hide()
		self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
		self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
		self.tableWidget.setShowGrid(False)
		self.tableWidget.customContextMenuRequested.connect(self.__popupAt)
		self.tableWidget.currentCellChanged.connect(self.__cellChanged)
		self.tableWidget.cellDoubleClicked.connect(self.__cellActivated)

		verticalLayout.addWidget(self.tableWidget)

	def setSortColumn(self, column = None, toggle = False):
		if column is None: column = self.__sort_column

		order = self.tableWidget.horizontalHeader().sortIndicatorOrder()
		if toggle and column == self.__sort_column:
			if order == Qt.DescendingOrder : order = Qt.AscendingOrder
			elif order == Qt.AscendingOrder : order = Qt.DescendingOrder

		self.__sort_column = column
		if self.__sort_column > 0:
			self.tableWidget.sortItems(0, Qt.AscendingOrder)
		self.tableWidget.sortItems(self.__sort_column, order)

	def sort_column(self):
		return [self.__sort_column, int(self.tableWidget.horizontalHeader().sortIndicatorOrder())]

	def setFilter(self, text = None):
		if text is None or len(text) == 0:
			for i in range(self.tableWidget.rowCount()):
				self.tableWidget.setRowHidden(i, False)
		else:
			text = utils.string_unicode(text)
			for i in range(self.tableWidget.rowCount()):
				match = False
				cell = self.tableWidget.item(i, 0)
				if cell is not None and cell.contains(text):
					match = True

				self.tableWidget.setRowHidden(i, not match)

	def select_task(self, task_id):
		selected = False
		if self.task_id != task_id:
			for i in range(self.tableWidget.rowCount()):
				cell = self.tableWidget.item(i, 0)
				if cell is not None and cell.id == task_id:
					self.tableWidget.setCurrentCell(i, 0)
					self.tableWidget.scrollToItem(cell)
					selected = True
					break
		else:
			selected = True

		return selected

	def set_task(self, task):
		updated = False
		if task is None: return updated
		for i in range(self.tableWidget.rowCount()):
			cell = self.tableWidget.item(i, 0)
			if cell is not None and cell.id == task["id"]:
				updated = True
				# Prevent sorting during changes
				self.tableWidget.setSortingEnabled(False)
				# Old widget will be deleted by table
				self.tableWidget.setCellWidget(i, 0, self.__makeTaskWidget(task, not self.__tree_display))
				# Update existing fields
				self.tableWidget.item(i, 0).initData(task)
				self.tableWidget.item(i, 1).setText(str(task["status_order"]))
				self.tableWidget.item(i, 2).setText(task["activity"])
				self.tableWidget.item(i, 3).setText(str(task["end"]))
				self.tableWidget.item(i, 4).setText(str(task["order"]))
				self.tableWidget.item(i, 5).setText(task["path"])

				self.tableWidget.setSortingEnabled(True)
				break
		return updated

	def setTasks(self, tasks):
		self.tableWidget.clear()
		self.tableWidget.setRowCount(0)
		self.task_id = None

		if tasks is not None:
			# Prevent sorting during changes
			self.tableWidget.setSortingEnabled(False)
			self.tableWidget.setRowCount(len(tasks))

			for i, task in enumerate(tasks.values()):
				self.tableWidget.setCellWidget(i, 0, self.__makeTaskWidget(task, not self.__tree_display))
				self.tableWidget.setItem(i, 0, TaskItem(task))
				self.tableWidget.setItem(i, 1, QTableWidgetItem(str(task["status_order"])))
				self.tableWidget.setItem(i, 2, QTableWidgetItem(task["activity"]))
				self.tableWidget.setItem(i, 3, QTableWidgetItem(str(task["end"])))
				self.tableWidget.setItem(i, 4, QTableWidgetItem(str(task["order"])))
				self.tableWidget.setItem(i, 5, QTableWidgetItem(task["path"]))

			for i in range(1, COLUMN_COUNT):
				self.tableWidget.setColumnHidden(i, True)

			self.tableWidget.setCurrentCell(-1, -1)
			self.tableWidget.setSortingEnabled(True)
			self.setSortColumn()
			self.setFilter()
			self.tableWidget.scrollToTop()

	def __popupAt(self, pos):
		index = self.tableWidget.indexAt(pos)
		if not index.isValid(): return

		taskPath = None
		taskCerebro = None
		if self.task_id is not None:
			task = self.conn.task(self.task_id)
			if task is not None:
				task_paths = self.config.translate(task)
				taskCerebro = task["path"] + task["name"]
				taskPath = task_paths["publish"] if len(task_paths.get("publish", "")) > 0 else task_paths.get("version", None)

				menu_options = ["Open in Cerebro...", None, "Copy local path to Clipboard", "Show in Explorer..."]
				res = wapp.menu(task, self.tableWidget.viewport().mapToGlobal(pos), menu_options, "menu_task")
				if res is not None:
					if res in menu_options and len(taskPath) and len(taskCerebro):
						if res == menu_options[0]:
							webbrowser.open(utils.string_unicode(r"cerebro://{0}?tid={1}").format(taskCerebro, self.task_id))
						elif res == menu_options[2]:
							capp.copyToClipboard(taskPath)
						elif res == menu_options[3]:
							if not utils.show_dir(taskPath):
								wapp.error("Directory does not exist: {}".format(taskPath))
					else:
						# Hook used - update task data
						self.refresh.emit()

	def __cellChanged(self, newRow, newCol, lastRow = 0, lastCol = 0):
		item = self.tableWidget.item(newRow, 0)

		if item is not None:
			self.task_id = item.id
			self.clicked.emit()

	def __cellActivated(self, row, col):
		item = self.tableWidget.item(row, 0)

		if item is not None:
			self.task_id = item.id
			self.doubleClicked.emit()

	def __makeTaskWidget(self, task = None, fullInfo = True):
		wgt = QWidget()

		if task is not None:
			wgt.setFixedSize(400, 80)

			horizontalLayout = QHBoxLayout()
			horizontalLayout.setContentsMargins(0, 0, 15, 0)
			horizontalLayout.setSpacing(10)

			thumbFrame = QFrame(wgt)
			thumbFrame.setFrameShape(QFrame.StyledPanel)
			thumbFrame.setFrameShadow(QFrame.Raised)
			thumbFrame.setFixedSize(146, 80)

			taskThumb = QLabel(thumbFrame)
			taskThumb.setFixedSize(146, 80)
			taskThumb.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
			taskThumb.setObjectName("thumb")

			iconfile = task["thumbnail"]
			logo = QImage(iconfile).scaled(146, 80, Qt.KeepAspectRatioByExpanding) if iconfile is not None else QImage()

			show_folder = not fullInfo and task["is_folder"]

			if logo.isNull() and not show_folder:
				iconfile = utils.getResDir("image.png")
				logo = QImage(iconfile)

			if not logo.isNull():
				taskThumb.setPixmap(QPixmap.fromImage(logo))
			
			if show_folder:
				folderIcon = QLabel(thumbFrame)
				# Css property now
				#icon = QImage(utils.getResDir("folder-overlay.png"))
				#folderIcon.setPixmap(QPixmap.fromImage(icon))
				folderIcon.setFixedSize(146, 80)
				folderIcon.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
				folderIcon.setObjectName("folder-hover-hide")

			if task["indicator"] is not None:
				task_indicator = IndicatorWidget(task["indicator"], thumbFrame)
	
			verticalLayout = QVBoxLayout()
			verticalLayout.setContentsMargins(0, 0, 0, 0)
			verticalLayout.setSpacing(0)

			if fullInfo:
				pathname = task["path"].split('/')[-2]

				pathLabel = QLabel(pathname, wgt)
				pathLabel.setObjectName("header")
				pathLabel.setWordWrap(True)
				pathLabel.setToolTip(task["path_repr"])
				verticalLayout.addWidget(pathLabel)
				
				nameLabel = QLabel(task["name"], wgt)
				nameLabel.setObjectName("active")
				verticalLayout.addWidget(nameLabel)
				
				prjLabel = QLabel(task["path"].split('/')[1], wgt)
				verticalLayout.addWidget(prjLabel)
				
			else:
				nameLabel = QLabel(task["name"], wgt)
				nameLabel.setObjectName("header")
				verticalLayout.addWidget(nameLabel)

			if fullInfo or not task["is_folder"]:
				horizontalLayout_2 = QHBoxLayout()
				horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
				horizontalLayout_2.setSpacing(0)

				deadlineLabel = QLabel("Deadline: ", wgt)
				text = task["end"].strftime("%d %B %Y")
				if not utils.PY3: text = text.decode(locale.getpreferredencoding())
				deadlineDate = QLabel(text, wgt)
				deadlineDate.setObjectName("active")
				horizontalSpacer = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

				horizontalLayout_2.addWidget(deadlineLabel)
				horizontalLayout_2.addWidget(deadlineDate)
				horizontalLayout_2.addItem(horizontalSpacer)

				verticalLayout.addLayout(horizontalLayout_2)

			horizontalSpacer_2 = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

			taskStatus = QLabel(wgt)
			taskStatus.setFixedSize(26, 26)
			icon = QPixmap()
			if task["status_icon"] is not None and len(task["status_icon"]):
				icon = QIcon(task["status_icon"]).pixmap(QSize(20, 20))
			elif task["status_xpm"] is not None and len(task["status_xpm"]):
				icon.loadFromData(task["status_xpm"], "XPM")
				icon = icon.scaled(QSize(20, 20), Qt.KeepAspectRatio, Qt.SmoothTransformation)
			taskStatus.setPixmap(icon)
			taskStatus.setToolTip(task["status"])

			horizontalLayout.addWidget(thumbFrame)
			horizontalLayout.addLayout(verticalLayout)
			horizontalLayout.addItem(horizontalSpacer_2)
			horizontalLayout.addWidget(taskStatus)

			wgt.setLayout(horizontalLayout)

		return wgt

class TaskItem(QTableWidgetItem):
	def __init__(self, task):
		super(TaskItem, self).__init__()
		self.initData(task)

	def initData(self, task):
		if task is not None:
			self.id = task["id"]
			self.name = task["name"].lower()
			self.path = task["path"].lower()

	def contains(self, text):
		match = False

		if text is not None:
			if text.lower() in self.name: match = True
			if text.lower() in self.path: match = True

		return match

	def __lt__(self, other):
		if self.name == other.name:
			return self.path < other.path
		return self.name < other.name

	def text(self):
		return ""

class IndicatorWidget(QWidget):
	def __init__(self, color, parent):
		super(IndicatorWidget, self).__init__(parent)
		self.setFixedSize(20, 20)
		self.color = color

	def paintEvent(self, event):
		qp = QPainter(self)
		qp.setRenderHint(QPainter.Antialiasing, True)
		qp.setBrush(QBrush(QColor(self.color)))
		qp.setPen(Qt.NoPen)
		qp.drawEllipse(6, 6, 12, 12)

		super(IndicatorWidget, self).paintEvent(event)