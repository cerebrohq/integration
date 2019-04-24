# -*- coding: utf-8 -*-
import locale
from tentaculo.gui import style
from tentaculo.core import utils

from tentaculo.Qt.QtGui import *
from tentaculo.Qt.QtCore import *
from tentaculo.Qt.QtWidgets import *


class TaskHeader(QFrame):
	refresh = Signal()

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
		self.setObjectName("tasksHeader")
		self.setFixedHeight(97)

		verticalLayout = QVBoxLayout(self)
		verticalLayout.setContentsMargins(20, 10, 20, 15)
		verticalLayout.setSpacing(0)

		horizontalLayout_3 = QHBoxLayout()
		horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
		horizontalLayout_3.setSpacing(5)

		self.lb_taskLock = QLabel(self)
		self.lb_taskLock.setFixedSize(16, 16)
		self.lb_taskLock.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
		self.lb_taskLock.setPixmap(QPixmap(utils.getResDir("lock.png")))
		self.lb_taskLock.setVisible(False)

		self.lb_taskName = QLabel(self)
		self.lb_taskName.setObjectName("header")

		horizontalSpacer_3 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

		horizontalLayout_3.addWidget(self.lb_taskLock)
		horizontalLayout_3.addWidget(self.lb_taskName)
		horizontalLayout_3.addItem(horizontalSpacer_3)

		horizontalLayout_4 = QHBoxLayout()
		horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
		horizontalLayout_4.setSpacing(5)

		self.lb_taskPath = QLabel(self)
		self.lb_taskPath.setObjectName("active")

		self.pb_refresh = QPushButton("Refresh", self)
		self.pb_refresh.setObjectName("smallDark")
		self.pb_refresh.setFixedHeight(20)
		self.pb_refresh.setFixedWidth(80)
		self.pb_refresh.clicked.connect(self.refresh.emit)

		horizontalLayout_4.addWidget(self.lb_taskPath)
		horizontalLayout_4.addItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
		horizontalLayout_4.addWidget(self.pb_refresh)

		horizontalLayout = QHBoxLayout()
		horizontalLayout.setContentsMargins(0, 0, 0, 0)
		horizontalLayout.setSpacing(0)

		frame = QFrame(self)
		frame.setFrameShape(QFrame.StyledPanel)
		frame.setFrameShadow(QFrame.Raised)
		frame.setObjectName("tasksStatus")
		frame.setFixedWidth(401)

		horizontalLayout_2 = QHBoxLayout(frame)
		horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
		horizontalLayout_2.setSpacing(5)

		label = QLabel("STATUS:", frame)

		self.lb_taskStatusIcon = QLabel(frame)
		self.lb_taskStatusIcon.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

		self.lb_taskStatus = QLabel(frame)
		self.lb_taskStatus.setObjectName("active")

		self.lb_taskUser = QLabel(frame)
		self.lb_taskUser.setObjectName("active")

		horizontalSpacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

		horizontalLayout_2.addWidget(label)
		horizontalLayout_2.addWidget(self.lb_taskStatusIcon)
		horizontalLayout_2.addWidget(self.lb_taskStatus)
		horizontalLayout_2.addWidget(self.lb_taskUser)
		horizontalLayout_2.addItem(horizontalSpacer)

		label_2 = QLabel("DEADLINE: ", self)

		self.lb_taskDeadline = QLabel("", self)
		self.lb_taskDeadline.setObjectName("active")

		horizontalSpacer_2 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

		horizontalLayout.addWidget(frame)
		horizontalLayout.addWidget(label_2)
		horizontalLayout.addWidget(self.lb_taskDeadline)
		horizontalLayout.addItem(horizontalSpacer_2)

		verticalLayout.addLayout(horizontalLayout_3)
		verticalLayout.addLayout(horizontalLayout_4)
		verticalLayout.addLayout(horizontalLayout)

		self.setLayout(verticalLayout)

	def clearTask(self):
		self.lb_taskName.clear()
		self.lb_taskPath.clear()
		self.lb_taskStatus.clear()
		self.lb_taskUser.clear()
		self.lb_taskStatusIcon.clear()
		self.lb_taskDeadline.clear()
		self.lb_taskLock.setVisible(False)
		self.lb_taskName.setEnabled(True)

	def setTask(self, task = None):
		if task is None: return False

		self.lb_taskLock.setVisible(not task["enabled_task"])
		self.lb_taskName.setEnabled(task["enabled_task"])

		self.lb_taskName.setText(task["name"]) #
		self.lb_taskPath.setText(task["path_repr"])
		self.lb_taskStatus.setText(task["status"])
		self.lb_taskUser.setText(u": {0}".format(task["uname"]) if task["owned_user_id"] is not None else "")
		icon = QPixmap()
		icon.loadFromData(task["status_icon"], "XPM")
		self.lb_taskStatusIcon.setPixmap(icon)
		text = task["end"].strftime("%d %B %Y %H:%M")
		if not utils.PY3: text = text.decode(locale.getpreferredencoding())
		self.lb_taskDeadline.setText(text)

		return True
