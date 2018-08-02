# -*- coding: utf-8 -*-
import tentaculo
import tentaculo.api
import tentaculo.api.icerebro
import tentaculo.api.icerebro.cargo
import tentaculo.api.icerebro.db
	
try:
	import tentaculo.api.imaya
	import tentaculo.api.imaya.cerebroMaya
	import tentaculo.api.imaya.userSetup
except ImportError:
		pass
		
import tentaculo.core
import tentaculo.core.jsonio
import tentaculo.core.config
import tentaculo.core.shot
import tentaculo.core.capp
import tentaculo.core.clogger
import tentaculo.core.paths
import tentaculo.core.vfile
import tentaculo.core.fmanager
import tentaculo.gui.elements
import tentaculo.gui.elements.tasklist
import tentaculo.gui.elements.filelist
import tentaculo.gui.elements.taskheader
import tentaculo.gui.elements.taskcontrols
import tentaculo.gui.elements.taskdefinition
import tentaculo.gui.sendreport
import tentaculo.gui.showimg
import tentaculo.gui.style
import tentaculo.gui.taskwindow
import tentaculo.gui.wapp
import tentaculo.gui.wlinkedfiles
import tentaculo.gui.wlogin
import tentaculo.gui.wabout

if tentaculo.core.capp.PY3:
	from importlib import reload

def reload_modules():

	try:
		from tentaculo import debug
		reload(tentaculo.debug)
	except ImportError:
		pass	

	reload(tentaculo							)
	reload(tentaculo.api						)
	reload(tentaculo.api.icerebro				)
	reload(tentaculo.api.icerebro.cargo			)
	reload(tentaculo.api.icerebro.db			)	
	try:
		reload(tentaculo.api.imaya					)
		reload(tentaculo.api.imaya.cerebroMaya		)
		reload(tentaculo.api.imaya.userSetup		)
	except AttributeError:
		pass

	reload(tentaculo.core					)
	reload(tentaculo.core.capp				)
	reload(tentaculo.core.paths				)
	reload(tentaculo.core.config			)
	reload(tentaculo.core.clogger			)
	reload(tentaculo.core.jsonio			)
	reload(tentaculo.core.shot				)
	reload(tentaculo.core.vfile				)
	reload(tentaculo.core.fmanager			)
	reload(tentaculo.gui.elements			)
	reload(tentaculo.gui.elements.tasklist	)
	reload(tentaculo.gui.elements.filelist	)
	reload(tentaculo.gui.elements.taskheader)
	reload(tentaculo.gui.elements.taskcontrols)
	reload(tentaculo.gui.elements.taskdefinition)
	reload(tentaculo.gui.sendreport			)
	reload(tentaculo.gui.showimg			)
	reload(tentaculo.gui.style				)
	reload(tentaculo.gui.taskwindow			)	
	reload(tentaculo.gui.wapp				)
	reload(tentaculo.gui.wlogin				)
	reload(tentaculo.gui.wabout				)
	reload(tentaculo.gui.wlinkedfiles		)
