# -*- encoding: utf-8 -*-

import os
import sys
import json
import uuid
import urllib2
import base64

from ConfigParser import ConfigParser

baseurl = 'http://221.180.20.232:9001/api'


def generateId():
	return str(uuid.uuid4()).replace('-','')

def getUploadSession(length):
	req = urllib2.Request(baseurl + '/videoid')
	req.add_header('Content-Type', 'application/json')

	content = ''
	try:
		response = urllib2.urlopen(req, json.dumps({
			'UserKey'	: generateId(),
			'Length'		: length,
			}))
		content = response.read()

	except Exception, e:
		print e

	return json.loads(content)


def getUploadProgress(id):
	req = urllib2.Request(baseurl + '/upload_progress')
	req.add_header('Content-Type', 'application/json')

	content = ''
	try:
		response = urllib2.urlopen(req, json.dumps({
			'UserKey'	: generateId(),
			'VID'		: id,
			}))
		content = response.read()

	except Exception, e:
		print e

	return json.loads(content)


def postData(id, length, offset, bdata):
	req = urllib2.Request(baseurl + '/upload')
	req.add_header('Content-Type', 'application/json')

	try:
		response = urllib2.urlopen(req, json.dumps({
			'UserKey'	: id,
			'VID'		: id,
			'Length'		: length,
			'Offset'		: offset,
			'Size'		: len(bdata),
			'Data'		: base64.b64encode(bdata),
			}))

		return json.loads(response.read())
	except Exception, e:
		print e

	return None


applicationConfig = ConfigParser()
applicationConfig.read('Config.ini')
baseurl = applicationConfig.get('Test', 'Baseurl')
print baseurl
if len(sys.argv) > 1:
	buffer_size = 1024
	if len(sys.argv) > 2:
		buffer_size = int(sys.argv[2])
	filename = sys.argv[1]
	fsize = os.path.getsize(filename)
	session = getUploadSession(fsize)
	print session
	f = open(filename, 'rb')
	offset = 0L
	id = session['VID']

	while True:
		bdata = f.read(buffer_size)
		if bdata is None or len(bdata) == 0:
			break;

		postData(id, fsize, offset, bdata)
		offset += len(bdata)

		p = getUploadProgress(id)
		print str(int(p['Saved'] * 100 / p['Length'])) + '%'
else:
	print "Usage: %s <uploadfile> [<buffer_size>]" % sys.argv[0]
