# -*- coding: utf-8 -*-
import cerebro
from ctentaculo.tentaculo import version
import ctentaculo.install


def init_actions():
	main()


def main():
	add_menu()


def add_menu():
	ver_installed = ctentaculo.install.getPrevVersion()
	icon = '' #cerebro.core.python_api_dir() + '/tentaculo/icon.png'
	#user = cerebro.core.user_profile()
	mainMenu = cerebro.actions.MainMenu()
	#if not mainMenu.has_menu('Tentaculo'):
	userMenu = mainMenu.insert_menu(mainMenu.size() - 1, 'Tentaculo')
	userMenu.add_action('ctentaculo.install.install', 'Install', icon)
	if ver_installed[0] > 0:
		userMenu.add_action('ctentaculo.install.uninstall', 'Uninstall v{0}'.format(ver_installed[1]), icon)

	cerebro.actions.MessageForumToolBar().add_action('ctentaculo.browse.browse', 'Browse Task', '')
	cerebro.actions.TaskNavigatorMenu().add_action('ctentaculo.browse.make_dirs',  'Make Directories' , '')

def remove_menu():
	mainMenu = cerebro.actions.MainMenu()
	mainMenu.remove_menu('tentaculo')
