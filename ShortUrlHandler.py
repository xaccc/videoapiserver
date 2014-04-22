#-*- encoding: utf-8 -*-

import os,logging
import uuid, hashlib, json
import time, signal, multiprocessing
import httplib, tornado.web, tornado.ioloop, tornado.httpserver
import dateutil, dateutil.tz, dateutil.parser
import logging
import NumberCodec

from MySQL import MySQL
from ConfigParser import ConfigParser


__config = ConfigParser()
__config.read('Config.ini')
__short_url_prefix = __config.get('ShortUrl','Prefix')



class ShortUrlHandler(tornado.web.RequestHandler):

	def get(self, numStr):
		num = NumberCodec.decode(numStr)
		# first find
		urlInstance = getDB().get(r"SELECT * FROM `short_urls` WHERE `id`=%s", num)
		if urlInstance:
			self.redirect(urlInstance['url'])
			# log
			db.save(r"INSERT INTO `short_urls_log` (`url_id`) VALUES (%s)", (num))
			db.end()
		else:
			raise tornado.web.HTTPError(404)


def getDB():
	return MySQL({
				'host'  : __config.get('Database','Host'),
				'port'  : __config.getint('Database','Port'),
				'user'  : __config.get('Database','User'),
				'passwd': __config.get('Database','Passwd'),
				'db'    : __config.get('Database','Database')})


def getShortUrl(url):
	urlId = 0
	db = getDB()
	urlhash = hashlib.md5(url).hexdigest()

	# first find
	urlInstance = db.get(r"SELECT * FROM `short_urls` WHERE `hash`=%s", urlhash)
	if urlInstance:
		urlId = urlInstance['id']

	# create if don't found
	if urlId == 0:
		result = db.save(r"INSERT INTO `short_urls` (`hash`, `url`) VALUES (%s,%s)", (urlhash, url))
		urlId = db.getInsertId()
		db.end()

	return __short_url_prefix + NumberCodec.encode(urlId)


if __name__ == "__main__":
	
	import sys

	if len(sys.argv) > 1:
		print getShortUrl(sys.argv[1])
	else:
		print getShortUrl('http://www.tornadoweb.cn/en/documentation')
