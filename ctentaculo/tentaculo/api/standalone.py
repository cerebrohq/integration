# -*- coding: utf-8 -*-
import sys, socket, json

from tentaculo.core import utils
from tentaculo.gui import wapp

SERVER_PORT = 11000
VERSION_MAJOR = 1
VERSION_MINOR = 0
BUFF_SIZE = 1024

def recvall(sock):
	data = utils.string_byte("")
	while True:
		part = sock.recv(BUFF_SIZE)
		data += part
		if len(part) < BUFF_SIZE:
			# either 0 or end of data
			break
	return data

def message_function(name, args=[]):
	ret = None
	if message_check():
		snd = {
			"function" : name,
			"args": args,
			"versionMajor": VERSION_MAJOR,
			"versionMinor": VERSION_MINOR
		}
		ret = send_data(snd).get("args", [None])

	return ret

def message_check():
	snd = {
		"function" : "check",
		"args": [],
		"versionMajor": VERSION_MAJOR,
		"versionMinor": VERSION_MINOR
	}
	ret = send_data(snd).get("args", [None])

	return ret[0] == "OK"

def send_data(data):
	msg = utils.string_byte(json.dumps(data))
	response = send_message(msg)
	res = json.loads(utils.string_unicode(response))

	return res

def send_message(message):
	response = {}
	
	try:
		server_address = ('localhost', SERVER_PORT + 1)
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		sock.connect(server_address)
		sock.sendall(message)

		response = recvall(sock)
		sock.close()
	except Exception as err:
		wapp.error(utils.error_unicode(err), "TCP connection error")

	return response
