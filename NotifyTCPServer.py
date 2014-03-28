#coding=utf-8
#-*- encoding: utf-8 -*-

import os
import threading, time
import struct
import signal
import json

from datetime import datetime
from tornado.tcpserver import TCPServer
from tornado.ioloop  import IOLoop
from tornado import process
from tornado import netutil
from ConfigParser import ConfigParser

from Server import MyJSONEncoder
from Service import Service


PACKET_HEADER_LEN = 6

NOTIFY_COMMAND_PING = 1
NOTIFY_COMMAND_REGISTER = 2
NOTIFY_COMMAND_SHAREVIDEO = 3

client_set = set()
client_set_lock = threading.Lock()

class Connection(object):


	def __init__(self, stream, address):

		client_set_lock.acquire()
		client_set.add(self)
		client_set_lock.release()

		self._lock = threading.Lock()
		self._last = datetime.now()
		self._stream = stream
		self._address = address
		self._userKey = ''
		self._userId = ''
		self._mobile = ''

		self._stream.set_close_callback(self.on_close)

		self.postReadHeader()

		print "Client connected: %s" % str(self._address)

	def __del__(self):
		self._lock

	def postReadHeader(self):
		self._command = -1
		self._stream.read_bytes(PACKET_HEADER_LEN, self.parseHeader)


	def parseHeader(self, data):
		self._last = datetime.now()

		sign,cmd,bodySize = struct.unpack('>2sHH', data)
		print "Header: sign=%s, command=%s, bodySize=%s   %s" % (sign, cmd, bodySize, self._address)

		if sign == 'NT':
			self._command = cmd
			self.postReadBody(bodySize)
		else:
			self._stream.close()

	def postReadBody(self, bodySize):
		self._stream.read_bytes(bodySize, self.parseBody)

	def parseBody(self, data):
		self._last = datetime.now()

		if self._command == NOTIFY_COMMAND_REGISTER:

			self._userKey = str(data)
			self._userId = service.getUserId(self._userKey)
			self._mobile = service.getUserMobile(self._userId)

			print "Client %s Register UserKey: %s" % (self._mobile, self._userKey)

		elif self._command == NOTIFY_COMMAND_PING:
			self.postMessage(NOTIFY_COMMAND_PING, data)

		else:
			print "Body: %s %s" % (str(data), self._address)


		self.postReadHeader() # read new packet


	def close(self, data):
		self._stream.close()


	def postMessage(self, cmd, msg):
		data = bytes(msg)
		self._lock.acquire()
		self._stream.write(struct.pack(">2sHH", "NT", cmd, len(data)))
		self._stream.write(data)
		self._lock.release()


	def on_close(self):
		print "Client %s disconnect UserKey: %s" % (self._mobile, self._userKey)
		client_set_lock.acquire()
		client_set.remove(self)
		client_set_lock.release()


	@staticmethod
	def sendNotify(userKey, cmd, message):
		try:
			client_set_lock.acquire()
			for (idx,client) in enumerate(client_set):
				if client._userKey == userKey:
					client.postMessage(cmd, message)
					break
		finally:
			client_set_lock.release()


	@staticmethod
	def ping_thread(service):
		while( not isShutdown.wait(60*30) ):
			print 'send ping to %s clients ...' % len(client_set)
			userKeys = []
			try:
				client_set_lock.acquire()
				for (idx,client) in enumerate(client_set):
					print client._userKey
					if len(client._userKey) > 0:
						userKeys.append(client._userKey);

			finally:
				client_set_lock.release()

			for (idx,userKey) in enumerate(userKeys):
				print 'send ping to %s ...' % userKey
				Connection.sendNotify(userKey, NOTIFY_COMMAND_PING, 'hello')


	@staticmethod
	def notify_thread(service):
		while True:
			if isShutdown.wait(0):
				break; # exit thread

			newNotify.wait(30)
			# 5sec 强制获取通知信息 
			sharelist = service.getShareList()
			for share in sharelist:
				try:
					client_set_lock.acquire()
					for (idx,client) in enumerate(client_set):
						if client._mobile == share['to_mobile']:
							data = {
								'From': share['mobile'],
								'To': share['to_mobile'],
								'Date': share['to_time'],
								'VID': share['video_id'],
							}
							client.postMessage(NOTIFY_COMMAND_SHAREVIDEO, json.dumps(data, cls=MyJSONEncoder))
				finally:
					client_set_lock.release()
		pass


class NotifyServer(TCPServer):

	def handle_stream(self, stream, address):
		Connection(stream, address)


isShutdown = threading.Event()
newNotify = threading.Event()

	
def sig_handler(sig, frame):
	isShutdown.set()	
	IOLoop.instance().add_callback(shutdown)


def shutdown():
	server.stop()

	io_loop = IOLoop.instance()
	deadline = time.time() + 3

	def stop_loop():
		now = time.time()
		if now < deadline and (io_loop._callbacks or io_loop._timeouts):
			io_loop.add_timeout(now + 1, stop_loop)
		else:
			io_loop.stop()

	stop_loop()


def startup():


	signal.signal(signal.SIGTERM, sig_handler)
	signal.signal(signal.SIGINT, sig_handler)

	applicationConfig = ConfigParser()
	applicationConfig.read('Config.ini')

	host = applicationConfig.get('NotifyServer','IP')
	port = applicationConfig.getint('NotifyServer','Listen')
	NumProcesses = applicationConfig.getint('NotifyServer','NumProcesses')

	pid = os.getpid()
	f = open('notifyserver.pid', 'wb')
	f.write(str(pid))
	f.close()

	global service
	service = Service(applicationConfig)
	threading.Thread(target=Connection.ping_thread, args=(service,)).start()
	threading.Thread(target=Connection.notify_thread, args=(service,)).start()

	print "Notify Server start on %s:%s (PID:%s) ..." % (host,port,pid)


	# sockets = netutil.bind_sockets(port,host)
	# process.fork_processes(NumProcesses)
	# global server
	# server = NotifyServer()
	# server.add_sockets(sockets)
	# IOLoop.instance().start()
	
	global server
	server = NotifyServer()
	server.listen(port,host)
	IOLoop.instance().start()

if __name__ == '__main__':
	startup()

