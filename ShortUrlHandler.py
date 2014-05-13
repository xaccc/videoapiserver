#-*- encoding: utf-8 -*-

import tornado.web
import NumberCodec
import ShortUrlService

from MySQL import MySQL


class ShortUrlHandler(tornado.web.RequestHandler):

	def get(self, numStr):
		num = NumberCodec.decode(numStr)
		db = MySQL()
		# first find
		urlInstance = db.get(r"SELECT * FROM `short_urls` WHERE `id`=%s", num)
		if urlInstance:
			self.redirect(urlInstance['url'])
			# log
			db.save(r"INSERT INTO `short_urls_log` (`url_id`) VALUES (%s)", (num))
			db.end()
		else:
			raise tornado.web.HTTPError(404)


	def set_default_headers(self):
		self.set_header('Server', 'Short URL Server')


