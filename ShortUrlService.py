#-*- encoding: utf-8 -*-

import NumberCodec
import Config
import Utils

from MySQL import MySQL


__short_url_prefix = Config.get('ShortUrl','Prefix')


def reverseShortUrl(shortUrl):
	result = None

	splitIdx = shortUrl.rindex('/')
	num = NumberCodec.decode(shortUrl[splitIdx+1:].split('?')[0]) if splitIdx >= 0 else NumberCodec.decode(shortUrl.split('?')[0])

	db = MySQL()
	# first find
	urlInstance = db.get(r"SELECT * FROM `short_urls` WHERE `id`=%s", num)
	if urlInstance:
		result = urlInstance['url']

	return result


def createShortUrl(url):
	urlId = 0
	db = MySQL()
	urlhash = Utils.MD5(url)

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

	surl = ''
	if len(sys.argv) > 1:
		surl = createShortUrl(sys.argv[1])
	else:
		surl = createShortUrl('http://www.tornadoweb.cn/en/documentation')

	print surl
	print reverseShortUrl(surl)
