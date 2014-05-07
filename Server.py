#coding=utf-8
#-*- encoding: utf-8 -*-

from datetime import date,datetime,timedelta
from urlparse import urljoin,urlsplit

from Downloader import Download
from Service import Service
from ShortUrlHandler import ShortUrlHandler
from APIHandler import APIHandler

import os,logging
import time, signal
import tornado.web, tornado.ioloop, tornado.httpserver
import Config,Utils


logging.basicConfig(filename = os.path.join(os.getcwd(), 'server.log'), level = logging.DEBUG)


def sig_handler(sig, frame):
	logging.warning('Caught signal: %s', sig)
	tornado.ioloop.IOLoop.instance().add_callback(shutdown)


def shutdown():
	logging.info('Stopping http server')
	http_server.stop()

	logging.info('Will shutdown in %s seconds ...', 5)
	io_loop = tornado.ioloop.IOLoop.instance()

	deadline = time.time() + 5

	def stop_loop():
		now = time.time()
		if now < deadline and (io_loop._callbacks or io_loop._timeouts):
			io_loop.add_timeout(now + 1, stop_loop)
		else:
			io_loop.stop()
			logging.info('Shutdown')

	stop_loop()


def startup():

	host = Config.get('Server','IP')
	port = Config.getint('Server','Listen')
	
	signal.signal(signal.SIGTERM, sig_handler)
	signal.signal(signal.SIGINT, sig_handler)

	pid = os.getpid()

	f = open('server.pid', 'wb')
	f.write(str(pid))
	f.close()

	application = tornado.web.Application([
		(r"/s/(.*)", ShortUrlHandler),
		(r"/api/(.*)", APIHandler),
		(r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "./static"}),
	])

	global http_server
	print "Startup server on %s:%d, PID:%d ..." % (host,port,pid)
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.bind(port, host)
	http_server.start(num_processes = Config.getint('Server','NumProcesses')) # tornado将按照cpu核数来fork进程
	tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
	startup()
