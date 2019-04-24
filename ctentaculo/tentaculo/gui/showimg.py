# -*- coding: utf-8 -*-

import sys, os

from tentaculo.Qt.QtGui import *
from tentaculo.Qt.QtCore import *
from tentaculo.Qt.QtWidgets import *

class w_showimg(QDialog):
	NAME = 'SHOW_IMG'
	TITLE = 'Show Image'

	def __init__(self, parent = None, pixmap=None):
		super(self.__class__, self).__init__(parent = None)
		self.pixmap = pixmap
		self.initUI()
		self.initStyle()
		self.initData()

	def initStyle(self):
		pass

	def initUI(self):
		#window init start
		self.setWindowFlags(Qt.Window)
		self.setObjectName(self.NAME)
		self.setWindowTitle('Cerebro: Show Image')
		self.resize(800, 600)
		#window init end

		self.gridLayout = QGridLayout(self)

		self.gb_img = QGroupBox(self)

		# img align layout
		self.vl1 = QVBoxLayout(self.gb_img)
		self.vl1.setAlignment(Qt.AlignCenter)
		# image gb
		self.label1 = QLabel(self.gb_img)
		self.vl1.addWidget(self.label1)
		# status
		self.statusbar = QStatusBar(self)
		self.statusbar.setMaximumHeight(20)

		# filling in grid
		self.gridLayout.addWidget(self.gb_img, 0, 0, 1, 1)
		self.gridLayout.addWidget(self.statusbar, 1, 0, 1, 1)

		self.setLayout(self.gridLayout)


	def initData(self):
		self.label1.setPixmap(self.pixmap)
		self.statusMsg('Click right mouse button to close the image viewer')

	def run(self):
		self.show()

	def stop(self):
		self.close()

	def closeEvent(self, event):
		self.close()

	def mousePressEvent(self, event):
		self.close()

	def statusMsg(self, msg = None):
		if msg is None: return
		self.statusbar.showMessage(msg)
