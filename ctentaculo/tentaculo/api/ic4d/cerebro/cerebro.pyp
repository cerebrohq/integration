import c4d
from c4d import gui, plugins

# TODO: Register
PLUGIN_ID = 10281843

class CerebroPlugin(plugins.CommandData):

	def Register(self):
		plug = plugins.RegisterCommandPlugin(
			PLUGIN_ID,
			"Cerebro Tentaculo",
			c4d.PLUGINFLAG_HIDEPLUGINMENU,
			None,
			"Cerebro Tentaculo",
			self
		)
		print("Loaded Cerebro plugin: {0}".format(plug))
		
	def Execute(self, doc):
		from tentaculo.api import menu
		menu.todolist()
		return True
		
	def GetSubContainer(self, doc, submenu):
		
		submenu.InsData(1, "Todo list")
		submenu.InsData(2, "Link/Embed")
		submenu.InsData(3, "Save as version")
		submenu.InsData(4, "Publish")
		submenu.InsData(5, "Logout")
		submenu.InsData(6, "Change working directory")
		submenu.InsData(7, "About")
		submenu.InsData(8, "Reload")
		
		return True
		
	def ExecuteSubID(self, doc, subid):
		from tentaculo.api import menu
		
		if subid == 1:
			menu.todolist()
		elif subid == 2:
			menu.browser()
		elif subid == 3:
			menu.createreport()
		elif subid == 4:
			menu.publish()
		elif subid == 5:
			menu.logout()
		elif subid == 6:
			menu.workdir()
		elif subid == 7:
			menu.about()
		elif subid == 8:
			menu.reload()
		
		return True


def EnchanceMainMenu():
	mainMenu = gui.GetMenuResource("M_EDITOR")
	pluginsMenu = gui.SearchPluginMenuResource()

	menu = c4d.BaseContainer()
	menu.InsData(c4d.MENURESOURCE_SUBTITLE, "Cerebro")
	menu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_10281843")

	if pluginsMenu:
		mainMenu.InsDataAfter(c4d.MENURESOURCE_STRING, menu, pluginsMenu)
	else:
		mainMenu.InsData(c4d.MENURESOURCE_STRING, menu)
	
def PluginMessage(id, data):
	if id == c4d.C4DPL_BUILDMENU:
		EnchanceMainMenu()
		return True
		
	return False

if __name__ == "__main__":
	CerebroPlugin().Register()
