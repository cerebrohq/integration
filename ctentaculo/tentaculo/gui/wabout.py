# -*- coding: utf-8 -*-
import sys, os, time

from tentaculo import version
from tentaculo.core import capp, utils
from tentaculo.gui import style

from tentaculo.Qt.QtGui import *
from tentaculo.Qt.QtCore import *
from tentaculo.Qt.QtWidgets import *


class w_about(QDialog):
	NAME = 'ABOUT_WINDOW'
	TITLE = 'About Cerebro Tentaculo'
	parent = None

	def __init__(self, parent = None):
		super(self.__class__, self).__init__(parent = parent)
		self.initUI()
		self.initStyle()

	def initStyle(self):
		styler = style.Styler()
		styler.initStyle(self)

	def initUI(self):
		self.setObjectName(self.NAME)
		self.setWindowTitle(self.TITLE)
		self.setFixedSize(220, 300)

		verticalLayout = QVBoxLayout(self)
		verticalLayout.setSpacing(10)
		verticalLayout.setContentsMargins(20, 20, 20, 20)
		verticalLayout.setAlignment(Qt.AlignHCenter)

		horizontalLayout = QHBoxLayout()
		horizontalLayout.setSpacing(0)
		horizontalLayout.setContentsMargins(0, 0, 0, 0)

		lb_logo = QLabel(self)
		lb_logo.setEnabled(True)
		lb_logo.setFixedSize(150, 210)
		lb_logo.setAlignment(Qt.AlignHCenter)
		lb_logo.setPixmap(QPixmap(utils.getResDir("cerebro.png")))

		horizontalLayout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
		horizontalLayout.addWidget(lb_logo)
		horizontalLayout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

		horizontalLayout_2 = QHBoxLayout()
		horizontalLayout_2.setSpacing(0)
		horizontalLayout_2.setContentsMargins(0, 0, 0, 0)

		lb_version = QLabel(u"{0} v{1}".format(version.APP_NAME, version.APP_VERSION), self)
		lb_version.setObjectName("active")

		horizontalLayout_2.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
		horizontalLayout_2.addWidget(lb_version)
		horizontalLayout_2.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

		horizontalLayout_3 = QHBoxLayout()
		horizontalLayout_3.setSpacing(0)
		horizontalLayout_3.setContentsMargins(0, 0, 0, 0)

		lb_link = QLabel(self)
		lb_link.setObjectName("active")
		lb_link.setText(r'Visit <a href="https://cerebrohq.com/">www.cerebrohq.com</a>')
		lb_link.setTextFormat(Qt.RichText)
		lb_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
		lb_link.setOpenExternalLinks(True)

		horizontalLayout_3.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
		horizontalLayout_3.addWidget(lb_link)
		horizontalLayout_3.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

		verticalLayout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
		verticalLayout.addLayout(horizontalLayout)
		verticalLayout.addLayout(horizontalLayout_2)
		verticalLayout.addLayout(horizontalLayout_3)
		verticalLayout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

	def run(self):
		self.showMinimized()
		self.showNormal()
		self.activateWindow()
		self.exec_()

	def stop(self):
		self.accept()
