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

	device = 'TEST'
	userKey = '0e32322a78d54bbbb5d20420f570ab70'

	api = ApiClient()
	#api = ApiClient(userKey)

	print '==============validate============='
	print json.dumps(api.validate('18636636365',device),sort_keys=False,indent=4)
	print '==============login============='
	print json.dumps(api.login('18636636365',device,'0147258369'),sort_keys=False,indent=4)
	print '==============user_id============='
	print json.dumps(api.user_id(),sort_keys=False,indent=4)

	exit() 


	buffer_size = 1024*100
	if len(sys.argv) > 2:
		buffer_size = int(sys.argv[2])
	filename = sys.argv[1]
	fsize = os.path.getsize(filename)
	session = api.uploadSession(fsize)
	print '==============uploadSession============='
	print json.dumps(session,sort_keys=False,indent=4)

	f = open(filename, 'rb')
	offset = 0L
	uploadId = session['UploadId']

	while True:
		p = api.uploadProgress(uploadId)
		print str(int(p['Saved'] * 100 / p['Length'])) + '%'


		if p['Saved'] == p['Length']:
			print 'Upload complete!'

			print "============================createVideo===================================="
			created = api.createVideo(uploadId)
			print json.dumps(created,sort_keys=False,indent=4)

			print "============================getVideo===================================="
			videoId = created.get('VID')
			video = api.getVideo(videoId)
			print json.dumps(video,sort_keys=False,indent=4)


			# share
			print "============================shreaVideo===================================="
			print json.dumps(api.shreaVideo(videoId, [
					{'Mobile': '18636636365', 'Name': '戴晶晶'},
					{'Mobile': '18636637312', 'Name': '南燕'},
					{'Mobile': '18636638800', 'Name': '薛博'},
					]),sort_keys=False,indent=4)

			# dwz
			print "============================shreaVideo===================================="
			print json.dumps(api.video_dwz(videoId),sort_keys=False,indent=4)

			# qrcode
			print "============================shreaVideo===================================="
			print json.dumps(api.video_qrcode(videoId),sort_keys=False,indent=4)

			# list 
			print "============================listShareVideo===================================="
			print json.dumps(api.listShareVideo(),sort_keys=False,indent=4)


			print "============================video_list===================================="
			print json.dumps(api.video_list(),sort_keys=False,indent=4)


		f.seek(p['Saved'],0)
		bdata = f.read(buffer_size)
		if bdata is None or len(bdata) == 0:
			break;

		res = api.upload(uploadId, fsize, offset, bdata)
		offset += len(bdata)
		print '==============uploadSession============='
		print json.dumps(res,sort_keys=False,indent=4)




else:
	print "Usage: %s <uploadfile> [<buffer_size>]" % sys.argv[0]
