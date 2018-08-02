import sys, os, time
from tentaculo.core import capp
from tentaculo.api import menu

if capp.HOST == capp.MAX:
	import MaxPlus

	MaxPlus.MenuManager.UnregisterMenu(u"Cerebro")

	mb = MaxPlus.MenuBuilder(u"Cerebro")

	action = MaxPlus.ActionFactory.Create("Cerebro", "Todo list", menu.todolist)
	mb.AddItem(action)
	action = MaxPlus.ActionFactory.Create("Cerebro", "Link/Embed", menu.browser)
	mb.AddItem(action)
	action = MaxPlus.ActionFactory.Create("Cerebro", "Save as version", menu.createreport)
	mb.AddItem(action)
	action = MaxPlus.ActionFactory.Create("Cerebro", "Publish", menu.publish)
	mb.AddItem(action)
	mb.AddSeparator()
	action = MaxPlus.ActionFactory.Create("Cerebro", "Logout", menu.logout)
	mb.AddItem(action)
	mb.AddSeparator()
	action = MaxPlus.ActionFactory.Create("Cerebro", "Change working directory", menu.workdir)
	mb.AddItem(action)
	mb.AddSeparator()
	action = MaxPlus.ActionFactory.Create("Cerebro", "About", menu.about)
	mb.AddItem(action)
	if capp.DEBUG is True:
		action = MaxPlus.ActionFactory.Create("Cerebro", "Reload", menu.reload)
		mb.AddItem(action)

	helpMenu = MaxPlus.MenuManager.GetMainMenu().GetNumItems()
	mb.Create(MaxPlus.MenuManager.GetMainMenu(), helpMenu - 1)
