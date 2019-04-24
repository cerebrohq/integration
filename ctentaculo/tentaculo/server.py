# -*- coding: utf-8 -*-
import sys, os

fdir = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir))
pydirs = [ r'python/python35.zip/lib', r'python/DLLs' ]

for p in [ os.path.normpath(os.path.join(fdir, p)) for p in pydirs ]:
	if not p in sys.path:
		sys.path.append(p)

import socket, json
from tentaculo.core import capp, utils
from tentaculo.api import menu, standalone

# WARNING: This is SINGLETON
class Server(object):
	__instance = None

	def __new__(cls, *args, **kwargs):
		if not isinstance(cls.__instance, cls):
			cls.__instance = super(Server, cls).__new__(cls, *args, **kwargs)
			cls.__instance()
		return cls.__instance
		
	def __call__(self):
		self.clear()

	def clear(self):
		self.sock = None
		self.flag_stop = False

	def start(self):
		server_address = ('localhost', standalone.SERVER_PORT)
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.bind(server_address)
		self.sock.listen(1)

		while not self.flag_stop:
			connection, client_address = self.sock.accept()
			data = standalone.recvall(connection)
			value = json.loads(utils.string_unicode(data))
			response = {
				"function" : value["function"],
				"args": [],
				"versionMajor": standalone.VERSION_MAJOR,
				"versionMinor": standalone.VERSION_MINOR
				}
			if value["function"] == "check":
				if int(value["versionMajor"]) == standalone.VERSION_MAJOR:
					response["args"] = ["OK"]
				else:
					response["args"] = ["Incompatible protocol version"]
				connection.sendall(utils.string_byte(json.dumps(response)))
				connection.close()

			elif value["function"] == "menu_todolist":
				connection.close()
				menu.todolist()

			elif value["function"] == "menu_browser":
				connection.close()
				menu.browser()
		
			elif value["function"] == "menu_createreport":
				connection.close()
				menu.createreport()

			elif value["function"] == "menu_publish":
				connection.close()
				menu.publish()
	
			elif value["function"] == "menu_logout":
				connection.close()
				menu.logout()

			elif value["function"] == "menu_workdir":
				connection.close()
				menu.workdir()
	
			elif value["function"] == "menu_about":
				connection.close()
				menu.about()

			elif value["function"] == "stop":
				self.flag_stop = True
				connection.close()

			else:
				response["args"] = ["Unknown function name"]
				connection.sendall(utils.string_byte(json.dumps(response)))
				connection.close()

		self.sock.close()
		return 0



if __name__ == "__main__":
	if len(sys.argv) > 2:
		standalone.SERVER_PORT = int(sys.argv[1])
		capp.set_standalone_host(sys.argv[2])

		server = Server()
		sys.exit(server.start())
