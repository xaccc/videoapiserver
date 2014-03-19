#coding=utf-8
#-*- encoding: utf-8 -*-

import os
import sys
import json
import uuid
import urllib2
import base64

from ApiClient import ApiClient





if len(sys.argv) > 1:

	api = ApiClient()

	device = 'DAI-MAC-MINI'
	
	print json.dumps(api.validate('18636636365',device))
	print json.dumps(api.login('18636636365',device,'0147258369'))

	buffer_size = 1024*100
	if len(sys.argv) > 2:
		buffer_size = int(sys.argv[2])
	filename = sys.argv[1]
	fsize = os.path.getsize(filename)
	session = api.uploadSession(fsize)
	print session

	f = open(filename, 'rb')
	offset = 0L
	id = session['VID']

	while True:
		bdata = f.read(buffer_size)
		if bdata is None or len(bdata) == 0:
			break;

		api.upload(id, fsize, offset, bdata)
		offset += len(bdata)

		p = api.uploadProgress(id)
		print str(int(p['Saved'] * 100 / p['Length'])) + '%'

		if p['Saved'] == p['Length']:
			print 'Upload complete!'
			print json.dumps(api.getVideo(id),sort_keys=True,indent=4)

else:
	print "Usage: %s <uploadfile> [<buffer_size>]" % sys.argv[0]
