# -*- coding: utf-8 -*-
from ctentaculo.tentaculo import version
import ctentaculo.install


def logon():
	ver_installed = ctentaculo.install.getPrevVersion()
	ver_current = version.APP_VERSION_INT
	
	if ver_installed[0] > 0 and ver_current > ver_installed[0]:
		ctentaculo.install.update()
