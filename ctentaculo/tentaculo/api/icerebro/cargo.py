# -*- coding: utf-8 -*-

import os, requests, errno

try:
	from pycerebro import dbtypes, cargador, cclib
except:
	try:
		from py_cerebro import dbtypes, cargador, cclib
	except:
		from py_cerebro2 import dbtypes, cargador, cclib

from tentaculo.core import paths, config, utils

XMLRPC_PORT = 4040
HTTP_PORT = 4080


class Cargo():

	log = None
	storages = {}
	current_uid = None
	
	def __init__(self, log):
		self.log = log
		self.conf = config.Config()
		self.clear()

	def clear(self):
		self.storages = {}
		self.current_uid = None

	def init_host(self, db):
		self.log.info('Cargador storage connect started...')
		storages = db.execute('select * from "siteList"()')

		self.current_uid = None
		# Connection
		# 0 - Cannot connect
		# 1 - Remote connection
		# 2 - Local connection
		self.storages = { int(storage[2]) : {"dns_addr": storage[3], "port": storage[9] if storage[9] is not None else HTTP_PORT, "local": storage[10],
									   "connection": 2 if storage[10] is not None else 1, "service": None, "paths": paths.Paths() } for storage in storages }

		for storage in storages:
			if self.connect_storage(int(storage[2]), True):
				self.current_uid = int(storage[2])
				break

		if self.current_uid is None:
			for storage in storages:
				if self.connect_storage(int(storage[2])):
					self.current_uid = int(storage[2])
					break

			if self.current_uid is None:
				raise Exception('Cargador not available')

	def connect_storage(self, uid, localonly = False):
		# No such uid available
		if uid is None or not uid in self.storages or self.storages[uid]["connection"] == 0: return False
		# Storage already connected
		if self.storages[uid]["service"] is not None: return True

		# Try local
		if self.storages[uid]["connection"] == 2:
			addrs = self.storages[uid]["local"].split(':')
			if len(addrs) > 1 and addrs[0]:
				try:
					carga = cargador.Cargador(addrs[0], XMLRPC_PORT, self.storages[uid]["port"])
					cargainfo = carga.statusInfo()
					if not cargainfo or len(cargainfo) < 2:
						raise Exception('Cargador do not have status info')

					info = cargainfo[1][0]
					#self.log.debug('Cargador status: %s', info)

					startstr = '... network path'
					start = info.find(startstr)
					if start == -1:
						startstr = '... local path'
						start = info.find(startstr)
						if start == -1:
							raise Exception('Cargador do not have network path')
							
					stop = info.find('\n', start)

					netpath = info[start + len(startstr):stop].strip()
						
					if len(netpath) == 0:
						raise Exception('Cargador do not have network path')

					self.log.debug('Cargador path: %s', netpath)
					cargapath = self.storages[uid]["paths"].add_auto_path(netpath)
					self.log.info('Cargador network path: %s', cargapath)
					if cargapath == '' or not os.path.exists(cargapath):
						raise Exception('Cargador %s path not available' % netpath)

					self.storages[uid]["service"] = carga

					self.log.info('Storage address %s',  addrs[0])
					self.log.info('Storage network path: %s', netpath)
					self.log.debug('Storage redirect paths %s',  self.storages[uid]["paths"].redirect_paths)
					self.log.info('Cargador storage connect has been successfully.')
					self.storages[uid]["connection"] = 2
						
				except Exception as err:
					self.log.debug('EXCEPTION', exc_info=1)
					self.log.error('Cargador %s:%s not loaded', addrs[0], XMLRPC_PORT)
					self.storages[uid]["connection"] = 1

		# Try remote?
		if localonly or self.storages[uid]["service"] is not None:
			return self.storages[uid]["service"] is not None

		try:
			carga = cargador.Cargador(self.storages[uid]["dns_addr"], XMLRPC_PORT, self.storages[uid]["port"])
			cargainfo = carga.statusInfo()
			if not cargainfo or len(cargainfo) < 2:
				raise Exception('Cargador do not have status info')

			self.storages[uid]["service"] = carga

			self.log.info('Storage address %s', self.storages[uid]["dns_addr"])
			self.log.info('Cargador storage connect has been successfully.')
			self.storages[uid]["connection"] = 1

		except Exception as err:
			self.log.debug('EXCEPTION', exc_info=1)
			self.log.error('Cargador %s:%s not loaded', self.storages[uid]["dns_addr"], XMLRPC_PORT)
			self.storages[uid]["connection"] = 0


		return self.storages[uid]["service"] is not None


	def file(self, hash):
		filepath = None
		if not self.current_uid in self.storages or self.storages[self.current_uid]["service"] is None or hash is None or len(hash) == 0:
			return filepath

		if self.storages[self.current_uid]["connection"] == 1:
			path = os.path.join(utils.tempdir() if self.conf.local_dir is None else self.conf.local_dir, ".cache", hash)

			if not os.path.exists(os.path.dirname(path)):
				try:
					os.makedirs(os.path.dirname(path))
				except OSError as err: # Guard against race condition
					if err.errno != errno.EEXIST:
						raise

			if not os.path.exists(path):
				host = '{0}:{1}'.format(self.storages[self.current_uid]["dns_addr"], self.storages[self.current_uid]["port"])
				headers = {
					"User-Agent": "Python downloader",
					"Content-type": "application/octet-stream",
					"Accept": "text/plain",
					"host": host,
					"accept-encoding": "gzip, deflate",
				}

				response = requests.get('http://{0}/file?hash={1}'.format(host, hash), headers=headers, stream=True)
				if response.status_code == 200:
					with open(path, 'wb') as fh:
						for chunk in response.iter_content(1024):
							fh.write(chunk)

					filepath = path
			else:
				filepath = path
				
		elif self.storages[self.current_uid]["connection"] == 2:
			try:
				#self.log.debug('hash %s', hash)
				hash64 = cclib.hash16_64(hash.upper())
				file_info = self.storages[self.current_uid]["service"].catalogResolve(hash64)
				if len(file_info) > 1:
					filepath = self.storages[self.current_uid]["paths"].redirect(file_info[1][0])
			except Exception as err:
				self.log.debug('EXCEPTION', exc_info=1)
		
		return filepath

	def service(self, uid = None):
		if uid is None: uid = self.current_uid

		return self.storages[uid]["service"] if self.connect_storage(uid) else None
