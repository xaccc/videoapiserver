#coding=utf-8
#-*- encoding: utf-8 -*-

import os, threading, time, struct, signal, json, socket

from datetime import datetime
from tornado.tcpserver import TCPServer
from tornado.ioloop  import IOLoop
from tornado import process, netutil
from ConfigParser import ConfigParser

import Config
import Utils
import ShareService


PACKET_HEADER_LEN = 6

NOTIFY_COMMAND_PING = 1
NOTIFY_COMMAND_REGISTER = 2
NOTIFY_COMMAND_SHAREVIDEO = 3
NOTIFY_COMMAND_NEWSHARED = 4


client_set = set()
client_set_lock = threading.Lock()


def send_to_server_newshare(userId):
	send_to_server(NOTIFY_COMMAND_NEWSHARED, userId)


def send_to_server(cmd, data):
	host = Config.get('NotifyServer','IP')
	port = Config.getint('NotifyServer','Listen')

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect((host, port))
	sock.send(struct.pack(">2sHH", "NT", cmd, len(data)))
	sock.send(data)
	time.sleep(1)
	sock.close()



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
		pass

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
		try:
			self._last = datetime.now()

			if self._command == NOTIFY_COMMAND_REGISTER:

				self._userKey = str(data)
				self._userId = service.getUserId(self._userKey)
				self._mobile = service.getUserMobile(self._userId)

				newNotify.set() # send new notify
				print "Client %s Register UserKey: %s" % (self._mobile, self._userKey)

			elif self._command == NOTIFY_COMMAND_PING:
				self.postMessage(NOTIFY_COMMAND_PING, data)

			elif self._command == NOTIFY_COMMAND_NEWSHARED:
				newNotify.set() # send new notify
				print "newshare: %s " % (data)

			else:
				print "Body: %s %s" % (str(data), self._address)
		except:
			self.close()

		self.postReadHeader() # read new packet


	def close(self):
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
	def ping_thread():
		while( not isShutdown.wait(60) ):
			userKeys = []
			try:
				client_set_lock.acquire()
				for (idx,client) in enumerate(client_set):
					if len(client._userKey) > 0:
						userKeys.append(client._userKey);

			finally:
				client_set_lock.release()

			for (idx,userKey) in enumerate(userKeys):
				Connection.sendNotify(userKey, NOTIFY_COMMAND_PING, 'hello')


	@staticmethod
	def notify_thread():
		while True:
			if isShutdown.wait(0):
				break; # exit thread

			newNotify.wait(600) # 10分钟 强制获取通知信息
			sharelist = ShareService.getShareList()
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
							ShareService.shareNotifyed(share['session_id'], share['to_mobile'])
				finally:
					client_set_lock.release()

			newNotify.clear()



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

	host = Config.get('NotifyServer','IP')
	port = Config.getint('NotifyServer','Listen')
	NumProcesses = Config.getint('NotifyServer','NumProcesses')

	pid = os.getpid()
	f = open('notifyserver.pid', 'wb')
	f.write(str(pid))
	f.close()

	threading.Thread(target=Connection.ping_thread).start()
	threading.Thread(target=Connection.notify_thread).start()

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

