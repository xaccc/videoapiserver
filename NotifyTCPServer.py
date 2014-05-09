#coding=utf-8
#-*- encoding: utf-8 -*-

import os, threading, time, struct, signal, json, socket

from datetime import datetime
from tornado.tcpserver import TCPServer
from tornado.ioloop  import IOLoop
from tornado import process, netutil
from MySQL import MySQL
from Queue import Queue

import Config
import Utils
import UserService, NotifyService

PACKET_HEADER_LEN = 6

NOTIFY_COMMAND_PING = 1
NOTIFY_COMMAND_REGISTER = 2
NOTIFY_COMMAND_NOTIFY = 3
NOTIFY_COMMAND_NEWNOTIFY = 4


client_set = set()
client_set_lock = threading.Lock()


def notify_server_has_new(userId):
	send_to_server(NOTIFY_COMMAND_NEWNOTIFY, userId)


def send_to_server(cmd, data):
	host = Config.get('NotifyServer','IP')
	port = Config.getint('NotifyServer','Listen')

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect((host, port))
	sock.send(struct.pack(">2sHH", "NT", cmd, len(data)))
	sock.send(data)
	time.sleep(1)
	sock.close()


def send_notify(userId=None):
	notifylist = NotifyService.list(userId)
	for notify in notifylist:
		try:
			client_set_lock.acquire()
			for (idx, client) in enumerate(client_set):
				if client._userId == notify['user_id']:
					client.postMessage(NOTIFY_COMMAND_NOTIFY, notify['notify'] if notify['notify'] else '')
					NotifyService.arrived(notify['id'])
		finally:
			client_set_lock.release()



class Connection(object):

	def __init__(self, stream, address):

		client_set_lock.acquire()
		client_set.add(self)
		client_set_lock.release()

		self._lock = threading.Lock()
		self._stream = stream
		self._address = address
		self._userId = ''

		self._stream.set_close_callback(self.on_close)
		print "[%s] Client Connected: %s" % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), str(self._address))

		self.postReadHeader()


	def postReadHeader(self):
		self._command = -1
		self._stream.read_bytes(PACKET_HEADER_LEN, self.parseHeader)


	def parseHeader(self, data):
		sign,cmd,bodySize = struct.unpack('>2sHH', data)

		if sign == 'NT':
			self._command = cmd
			self.postReadBody(bodySize)
		else:
			self._stream.close()


	def postReadBody(self, bodySize):
		self._stream.read_bytes(bodySize, self.parseBody)


	def parseBody(self, data):
		try:
			if self._command == NOTIFY_COMMAND_REGISTER:
				# data == userKey
				self._userId = UserService.getUserId(str(data))

				send_notify(self._userId)
				print "[%s] Client Register UserId: %s" % ( datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self._userId )

			elif self._command == NOTIFY_COMMAND_PING:
				self.postMessage(NOTIFY_COMMAND_PING, data)

			elif self._command == NOTIFY_COMMAND_NEWNOTIFY:
				# data == userId
				print "[%s] Has Notify UserId: %s " % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), data)
				send_notify(str(data))

			else:
				print "[%s] Unknown command: %s %s" % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), str(self._command), self._address)

		except Exception as e:
			print 'has error, to close connection! (%s)' % e
			self.close()

		self.postReadHeader() # read new packet


	def close(self):
		self._stream.close()


	def postMessage(self, cmd, msg):
		data = bytes(msg)
		self._lock.acquire()
		try:
			self._stream.write(struct.pack(">2sHH", "NT", cmd, len(data)))
			self._stream.write(data)
		finally:
			self._lock.release()


	def on_close(self):
		print "[%s] Client Disconnect: %s" % ( datetime.now().strftime('%Y-%m-%d %H:%M:%S'), str(self._address) )
		client_set_lock.acquire()
		client_set.remove(self)
		client_set_lock.release()



class NotifyServer(TCPServer):

	def handle_stream(self, stream, address):
		Connection(stream, address)

def sig_handler(sig, frame):
	IOLoop.instance().stop()

def startup():


	signal.signal(signal.SIGTERM, sig_handler)
	signal.signal(signal.SIGINT, sig_handler)

	host = Config.get('NotifyServer','IP')
	port = Config.getint('NotifyServer','Listen')
	NumProcesses = Config.getint('NotifyServer','NumProcesses')

	pid = os.getpid()
	f = open('notifyserver.pid', 'wb')
	f.write(str(pid))
	f.close()

	print "[%s] Notify Server start on %s:%s (PID:%s) ..." % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), host, port, pid)

	server = NotifyServer()
	server.listen(port,host)
	IOLoop.instance().start()

if __name__ == '__main__':
	startup()

