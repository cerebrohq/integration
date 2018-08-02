# -*- coding: utf-8 -*-
import sys, os, platform, tempfile


host_win = 'windows'
host_linux = 'linux'
host_macos = 'darwin'
host_current = platform.system().lower()

class Paths():

	redirect_paths = []

	def __init__(self):
		pass

	def add_paths(self, paths):

		redir = []
		valid_path = ''
		for path in paths: 
			path = os.path.normpath(path)			
			if os.path.exists(path):
				redir.insert(0, path)
				valid_path = path
			else:
				redir.append(path)	

		self.redirect_paths.append(redir)

		return valid_path

	def add_auto_path(self, path):
		valid_path = ''
		normpath = os.path.normpath(path)					
		if host_current == host_win:
			if not os.path.exists(normpath):
				if not normpath.startswith('\\\\') and normpath.startswith('\\'):
					newpath = '\\' + normpath
					if os.path.exists(newpath):
						redir = []
						redir.append(newpath)
						redir.append(normpath)
						redirect_paths.append(redir)				
						valid_path = newpath 
			else:
				valid_path = normpath 				
		
		elif host_current == host_linux:
			if not os.path.exists(normpath):
				if normpath.startswith('//'):
					newpath = normpath[1:]
					if os.path.exists(newpath):					
						redir = []
						redir.append(newpath)
						redir.append(normpath)
						self.redirect_paths.append(redir)				
						valid_path = newpath 
			else:
				valid_path = normpath

		elif host_current == host_macos:
			if not os.path.exists(normpath):
				if normpath.startswith('//'):
					dirs = normpath.split('/')
					newpath = '/Volumes'
					start = False
					for dir in dirs:
						if dir:
							if start:
								newpath = os.path.join(newpath, dir)
							start = True		
					
					if os.path.exists(newpath):					
						redir = []
						redir.append(newpath)
						redir.append(normpath)
						self.redirect_paths.append(redir)				
						valid_path = newpath 
			else:
				valid_path = normpath

		return valid_path

	def redirect(self, path):		
		if len(self.redirect_paths) > 0:
			path = path.replace('\\', '/')			
			for redir in self.redirect_paths:
				for i, dir in enumerate(redir):
					dir = dir.replace('\\', '/')
					if path.startswith(dir):
						if i != 0: # not self valid
							path = path.replace(dir, redir[0].replace('\\', '/'), 1)
						break

		return os.path.normpath(path)

	
		

