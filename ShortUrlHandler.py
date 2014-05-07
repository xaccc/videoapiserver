#-*- encoding: utf-8 -*-

import os,logging
import uuid, hashlib, json
import time, signal, multiprocessing
import httplib, tornado.web, tornado.ioloop, tornado.httpserver
import dateutil, dateutil.tz, dateutil.parser
import logging
import NumberCodec
import Config

from MySQL import MySQL

__short_url_prefix = Config.get('ShortUrl','Prefix')

class ShortUrlHandler(tornado.web.RequestHandler):

	def get(self, numStr):
		num = NumberCodec.decode(numStr)
		db = getDB()
		# first find
		urlInstance = db.get(r"SELECT * FROM `short_urls` WHERE `id`=%s", num)
		if urlInstance:
			self.redirect(urlInstance['url'])
			# log
			db.save(r"INSERT INTO `short_urls_log` (`url_id`) VALUES (%s)", (num))
			db.end()
		else:
			raise tornado.web.HTTPError(404)


def getDB():
	return MySQL()


def getUrl(shortUrl):
	result = None

	if shortUrl.index(__short_url_prefix) == 0:
		num = NumberCodec.decode(shortUrl[len(__short_url_prefix):].split('?')[0])
		db = getDB()
		# first find
		urlInstance = db.get(r"SELECT * FROM `short_urls` WHERE `id`=%s", num)
		if urlInstance:
			result = urlInstance['url']

	return result


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
