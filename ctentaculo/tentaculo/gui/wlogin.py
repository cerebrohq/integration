# -*- coding: utf-8 -*-
import sys, os, time

from tentaculo.core import capp, clogger, utils
from tentaculo.gui import style

from tentaculo.Qt.QtGui import *
from tentaculo.Qt.QtCore import *
from tentaculo.Qt.QtWidgets import *


class Wlogin(QDialog):
	NAME = 'LOGIN_WINDOW'
	TITLE = 'Login to Cerebro Tentaculo'
	parent = None	
	acc = None	
	login_as = None
	accounts = None
	__settings_visible = False

	def __init__(self, parent = None):
		QDialog.__init__(self, parent)
		self.log = clogger.CLogger().log
		# Pre-styling for old apps
		self.initStyle()
		self.initUI()
		self.initStyle()

	def initStyle(self):
		styler = style.Styler()
		styler.initStyle(self)

	def autologin(self):
		return self.cb_autologin.isChecked()

	def remember(self):
		return self.cb_rememberlogin.isChecked()

	def start_login(self, login_as, acc, autologin, remember, accounts):
		self.acc = acc				
		self.login_as = login_as
		self.cb_autologin.setChecked(autologin)
		self.cb_rememberlogin.setChecked(remember)
		self.accounts = accounts
		for account in self.accounts:
			login = account.get('login')
			if login:
				self.cb_username.addItem(login, account.get('id'))

		self.cb_username.blockSignals(True)
		for i in range(self.cb_username.count()):
			id = self.cb_username.itemData(i)
			if id == self.acc.get('id'):
				self.cb_username.setCurrentIndex(i)
				break
			
		self.cb_username.blockSignals(False)

		self.le_password.setText(str(self.acc.get('psw')))
		server, port = self.acc.get('address', ':').split(':')
		self.le_server.setText(server)
		self.le_port.setText(port)
		"""
		if capp.QT5:			
			self.cb_username.setCurrentText(self.acc.get('login'))
		else:
			self.cb_username.setEditText(self.acc.get('login'))
		"""		
		self.showMinimized()
		self.showNormal()
		self.activateWindow()
		res = self.exec_()

		if res == QDialog.Accepted:			
			return self.acc

		return None

	def trylogin(self):
		lgn = utils.string_unicode(self.cb_username.currentText()).lower().strip()
		psw = utils.string_unicode(self.le_password.text()).strip()
		srv = utils.string_unicode(self.le_server.text()).lower().strip()
		port = utils.string_unicode(self.le_port.text()).lower().strip()

		if lgn != '' and psw != '' and srv != '' and port != '':

			adr = ':'.join([srv, port])
			if self.acc.get('login', '') != lgn:
				acc = {}
				acc.setdefault('login', lgn)
				acc.setdefault('psw', psw)
				acc.setdefault('savepath', '')
				acc.setdefault('address', adr)
				self.acc = acc
		
			self.acc.update({'login': lgn})
			self.acc.update({'psw': psw})
			self.acc.update({'address': adr})

			if self.login_as(self.acc):
				self.accept()

	def change_account(self, index):

		id = None
		if not capp.QT5:
			id = self.cb_username.itemData(self.cb_username.currentIndex())
		else:
			id = self.cb_username.currentData()

		for account in self.accounts:
			if id == account.get('id'):
				self.acc = account
				self.le_password.setText(str(self.acc.get('psw')))
				server, port = self.acc.get('address', ':').split(':')
				self.le_server.setText(server)
				self.le_port.setText(port)
				break

	def toggle_settings(self):
		self.animation = QPropertyAnimation(self.fr_settings, b"maximumWidth")
		self.animation.setDuration(300)
		self.animation.setStartValue(220 if self.__settings_visible else 0)
		self.animation.setEndValue(0 if self.__settings_visible else 220)
		self.__settings_visible = not self.__settings_visible
		self.animation.start()
		
	def initUI(self):

		self.setObjectName(self.NAME)
		self.setWindowTitle(self.TITLE)
		self.setFixedSize(260, 460)

		verticalLayout_3 = QVBoxLayout(self)
		verticalLayout_3.setSpacing(10)
		verticalLayout_3.setContentsMargins(20, 20, 20, 20)
		verticalLayout_3.setAlignment(Qt.AlignHCenter)

		frame = QFrame(self)
		frame.setFrameShape(QFrame.StyledPanel)
		frame.setFrameShadow(QFrame.Raised)
		frame.setFixedHeight(30)

		horizontalLayout_2 = QHBoxLayout(frame)
		horizontalLayout_2.setSpacing(0)
		horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
		horizontalLayout_2.setAlignment(Qt.AlignRight)

		self.tb_settings = QToolButton(frame)
		self.tb_settings.setObjectName("loginSettings")
		self.tb_settings.setIconSize(QSize(24,24))
		self.tb_settings.setToolTip("Connection address")
		self.tb_settings.clicked.connect(self.toggle_settings)

		self.fr_settings = QFrame(frame)
		self.fr_settings.setFrameShape(QFrame.StyledPanel)
		self.fr_settings.setFrameShadow(QFrame.Raised)
		self.fr_settings.setMaximumWidth(0)

		horizontalLayout = QHBoxLayout(self.fr_settings)
		horizontalLayout.setSpacing(5)
		horizontalLayout.setContentsMargins(5, 0, 0, 0)

		self.le_server = QLineEdit(self.fr_settings)
		self.le_server.setObjectName("loginSettings")
		self.le_server.setPlaceholderText("Server")

		self.le_port = QLineEdit(self.fr_settings)
		self.le_port.setObjectName("loginSettings")
		self.le_port.setPlaceholderText("Port")
		self.le_port.setMaximumWidth(50)

		horizontalLayout.addWidget(self.le_server)
		horizontalLayout.addWidget(self.le_port)

		horizontalLayout_2.addWidget(self.tb_settings)
		horizontalLayout_2.addWidget(self.fr_settings)

		horizontalLayout_3 = QHBoxLayout()
		horizontalLayout_3.setSpacing(0)
		horizontalLayout_3.setContentsMargins(0, 0, 0, 0)

		self.lb_logo = QLabel(self)
		self.lb_logo.setEnabled(True)
		self.lb_logo.setFixedSize(150, 210)
		self.lb_logo.setAlignment(Qt.AlignHCenter)
		self.lb_logo.setPixmap(QPixmap(utils.getResDir("cerebro.png")))

		horizontalLayout_3.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
		horizontalLayout_3.addWidget(self.lb_logo)
		horizontalLayout_3.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

		self.cb_username = QComboBox(self)
		view = QListView(self.cb_username)
		self.cb_username.setView(view)
		self.cb_username.setObjectName("login")
		self.cb_username.setEditable(True)
		self.cb_username.lineEdit().setPlaceholderText("Login or E-mail")
		self.cb_username.lineEdit().setStyleSheet("QLineEdit {background: transparent;}")
		self.cb_username.setFocus()
		self.cb_username.currentIndexChanged.connect(self.change_account)

		self.le_password = QLineEdit(self)
		self.le_password.setObjectName("login")
		self.le_password.setEchoMode(QLineEdit.Password)
		self.le_password.setPlaceholderText("Password")

		horizontalLayout_4 = QHBoxLayout()
		horizontalLayout_4.setSpacing(0)
		horizontalLayout_4.setContentsMargins(0, 0, 0, 0)

		self.cb_rememberlogin = QCheckBox(self)
		self.cb_rememberlogin.setText("Remember me")
		self.cb_rememberlogin.setObjectName("login")
		self.cb_rememberlogin.stateChanged.connect(lambda st: self.cb_autologin.setChecked(False if st == Qt.Unchecked else self.cb_autologin.isChecked()))

		horizontalLayout_4.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
		horizontalLayout_4.addWidget(self.cb_rememberlogin)
		horizontalLayout_4.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

		horizontalLayout_5 = QHBoxLayout()
		horizontalLayout_5.setSpacing(0)
		horizontalLayout_5.setContentsMargins(0, 0, 0, 0)

		self.cb_autologin = QCheckBox(self)
		self.cb_autologin.setText("Auto login")
		self.cb_autologin.setObjectName("login")

		horizontalLayout_5.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
		horizontalLayout_5.addWidget(self.cb_autologin)
		horizontalLayout_5.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

		self.pb_login = QPushButton(self)
		self.pb_login.setObjectName("login")
		self.pb_login.setText("Login")
		self.pb_login.clicked.connect(self.trylogin)
		self.pb_login.setDefault(True)
		self.pb_login.setShortcut(QKeySequence(Qt.Key_Return))

		verticalLayout_3.addWidget(frame)
		verticalLayout_3.addLayout(horizontalLayout_3)
		verticalLayout_3.addWidget(self.cb_username)
		verticalLayout_3.addWidget(self.le_password)
		verticalLayout_3.addLayout(horizontalLayout_4)
		verticalLayout_3.addLayout(horizontalLayout_5)
		verticalLayout_3.addWidget(self.pb_login)
		verticalLayout_3.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
