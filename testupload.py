#coding=utf-8
#-*- encoding: utf-8 -*-

import os
import sys
import json
import uuid
import urllib2
import base64

from ConfigParser import ConfigParser

baseurl = 'http://127.0.0.1:9001/api'


def generateId():
	return str(uuid.uuid4()).replace('-','')


def postJSON(url,data):
	req = urllib2.Request(url)
	req.add_header('Content-Type', 'application/json')

	content = ''
	try:
		response = urllib2.urlopen(req, json.dumps(data))
		content = response.read()
		return json.loads(content)
	except Exception, e:
		print e
	
	return None

def uploadSession(length):
	return postJSON(baseurl + '/videoid', {
			'UserKey'	: generateId(),
			'Length'	: length,
			})


def uploadProgress(id):
	return postJSON(baseurl + '/upload_progress', {
			'UserKey'	: generateId(),
			'VID'		: id,
			})

def getVideo(id):
	return postJSON(baseurl + '/getvideo', {
			'UserKey'	: generateId(),
			'VID'		: id,
			})

def upload(id, length, offset, bdata):
	return postJSON(baseurl + '/upload', {
			'UserKey'	: id,
			'VID'		: id,
			'Length'	: length,
			'Offset'	: offset,
			'Size'		: len(bdata),
			'Data'		: base64.b64encode(bdata),
			})


applicationConfig = ConfigParser()
applicationConfig.read('Config.ini')
baseurl = applicationConfig.get('Test', 'Baseurl')
print baseurl
if len(sys.argv) > 1:
	buffer_size = 1024*100
	if len(sys.argv) > 2:
		buffer_size = int(sys.argv[2])
	filename = sys.argv[1]
	fsize = os.path.getsize(filename)
	session = uploadSession(fsize)
	print session

	f = open(filename, 'rb')
	offset = 0L
	id = session['VID']

	while True:
		bdata = f.read(buffer_size)
		if bdata is None or len(bdata) == 0:
			break;

		upload(id, fsize, offset, bdata)
		offset += len(bdata)

		p = uploadProgress(id)
		print str(int(p['Saved'] * 100 / p['Length'])) + '%'

		if p['Saved'] == p['Length']:
			print 'Upload complete!'
			print json.dumps(getVideo(id),sort_keys=True,indent=4)

else:
	print "Usage: %s <uploadfile> [<buffer_size>]" % sys.argv[0]
