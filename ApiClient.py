#coding=utf-8
#-*- encoding: utf-8 -*-

import os
import sys
import json
import uuid
import urllib2
import base64

import Config,Utils


baseURL = 'http://127.0.0.1:9001/api'


def generateId():
	return str(uuid.uuid4()).replace('-','')


class ApiClient(object):

	def __init__(self,userKey=''):
		self.userKey = userKey
		pass

	def __postJSON(self,url,data):
		req = urllib2.Request(url)
		req.add_header('Content-Type', 'application/json')

		content = ''
		try:
			response = urllib2.urlopen(req, json.dumps(data))
			content = response.read()
			return json.loads(content)
		except urllib2.HTTPError, e:
		    return json.loads(e.read())
		except urllib2.URLError, e:
		    print 'Reason: ', e.reason
		else:
			print e
		
		return None


	def user_validate(self,mobile,device):
		return self.__postJSON(baseURL + '/user_validate', {
				'Mobile'	: mobile,
				'Device'	: device,
				})


	def user_auth(self,id,device,validate):
		result = self.__postJSON(baseURL + '/user_auth', {
					'Id'		: id,
					'Device'	: device,
					'Validate'	: validate,
					})
		self.userKey = result['UserKey'] if result and result['UserKey'] else ''
		return result

	def user_id(self):
		return self.__postJSON(baseURL + '/user_id', {
				'UserKey'	: self.userKey,
				})


	def upload_id(self,length):
		return self.__postJSON(baseURL + '/upload_id', {
				'UserKey'	: self.userKey,
				'Length'	: length,
				})


	def upload_progress(self,id):
		return self.__postJSON(baseURL + '/upload_progress', {
				'UserKey'	: self.userKey,
				'UploadId'	: id,
				})


	def upload_data(self,id, length, offset, bdata):
		return self.__postJSON(baseURL + '/upload_data', {
				'UserKey'	: self.userKey,
				'UploadId'	: id,
				'Length'	: length,
				'Offset'	: offset,
				'Size'		: len(bdata),
				'Data'		: base64.b64encode(bdata),
				})


	def video_list(self, offset=0, listMax=10):
		return self.__postJSON(baseURL + '/video_list', {
				'UserKey'	: self.userKey,
				'Offset'	: offset,
				'Max'		: listMax
				})


	def video_create(self,id):
		return self.__postJSON(baseURL + '/video_create', {
				'UserKey'	: self.userKey,
				'UploadId'	: id,
				})


	def video_get(self,id):
		return self.__postJSON(baseURL + '/video_get', {
				'UserKey'	: self.userKey,
				'VID'		: id,
				})

	def video_ready(self,id):
		return self.__postJSON(baseURL + '/video_ready', {
				'UserKey'	: self.userKey,
				'VID'		: id,
				})

	def video_poster(self, vid, ss):
		return self.__postJSON(baseURL + '/video_poster', {
				'UserKey'	: self.userKey,
				'VID'		: vid,
				'Time'		: float(ss)
				})

	def video_dwz(self, vid):
		return self.__postJSON(baseURL + '/video_dwz', {
				'UserKey'	: self.userKey,
				'VID'		: vid
				})

	def video_qrcode(self, vid):
		return self.__postJSON(baseURL + '/video_qrcode', {
				'UserKey'	: self.userKey,
				'VID'		: vid
				})

	def share_video(self, id, toList):
		return self.__postJSON(baseURL + '/share_video', {
				'UserKey'	: self.userKey,
				'VID'		: id,
				'To'		: toList
				})

	def share_list(self, offset=0, listMax=10):
		return self.__postJSON(baseURL + '/share_list', {
				'UserKey'	: self.userKey,
				'Offset'	: offset,
				'Max'		: listMax
				})


	def short_url(self, url):
		return self.__postJSON(baseURL + '/short_url', {
				'URL' : url
				})

	def short_url_get(self, shortUrl):
		return self.__postJSON(baseURL + '/short_url_get', {
				'URL' : shortUrl
				})








baseURL = Config.get('Test', 'baseURL')



if __name__ == '__main__':
	# Unit Test
	api = ApiClient()
	#api = ApiClient(userKey)


	# test user_*
	device = 'TEST'
	print '==============user_validate============='
	print json.dumps(api.user_validate('18636636365',device),sort_keys=False,indent=4)
	print '==============user_auth============='
	print json.dumps(api.user_auth('18636636365',device,'0147258369'),sort_keys=False,indent=4)
	print '==============user_id============='
	print json.dumps(api.user_id(),sort_keys=False,indent=4)



	# test upload file
	if len(sys.argv) > 1:
		filename = sys.argv[1]
		fsize = os.path.getsize(filename)
		session = api.upload_id(fsize)
		print '==============upload_id============='
		print json.dumps(session,sort_keys=False,indent=4)

		f = open(filename, 'rb')
		offset = 0L
		uploadId = session['UploadId']

		while True:
			p = api.upload_progress(uploadId)
			print str(int(p['Saved'] * 100 / p['Length'])) + '%'

			if p['Saved'] == p['Length']:
				print 'Upload complete!'

				print "============================video_create===================================="
				created = api.video_create(uploadId)
				print json.dumps(created,sort_keys=False,indent=4)

				print "============================video_poster===================================="
				poster = api.video_poster(created['VID'], 3.0)
				print json.dumps(poster,sort_keys=False,indent=4)

				# share
				print "============================share_video===================================="
				print json.dumps(api.share_video(created['VID'], [
						{'Mobile': '18636636365', 'Name': '戴晶晶'},
						{'Mobile': '18636637312', 'Name': '南燕'},
						{'Mobile': '18636638800', 'Name': '薛博'},
						]),sort_keys=False,indent=4)

				break # upload finished

			buffer_size = 80*1024
			f.seek(p['Saved'],0)
			bdata = f.read(buffer_size)
			if bdata is None or len(bdata) == 0:
				break;

			res = api.upload_data(uploadId, fsize, offset, bdata)
			offset += len(bdata)


	# test video list
	print "============================share_list===================================="
	print json.dumps(api.share_list(listMax=2),sort_keys=False,indent=4)


	print "============================video_list===================================="
	video_list = api.video_list(listMax=2)
	print json.dumps(video_list,sort_keys=False,indent=4)

	if len(video_list['Results']) > 0:
		videoId = video_list['Results'][0]['VID']

		# video_get	
		print "============================video_get===================================="
		video = api.video_get(videoId)
		print json.dumps(video,sort_keys=False,indent=4)

		# video_get	
		print "============================video_ready===================================="
		video = api.video_ready(videoId)
		print json.dumps(video,sort_keys=False,indent=4)

		# video_dwz
		print "============================video_dwz===================================="
		print json.dumps(api.video_dwz(videoId),sort_keys=False,indent=4)

		# video_qrcode
		print "============================short_url===================================="
		surl = api.short_url(video_list['Results'][0]['VideoURLs'][0])
		print json.dumps(surl,sort_keys=False,indent=4)


		print "============================short_url_get===================================="
		print json.dumps(api.short_url_get(surl['SHORT_URL']),sort_keys=False,indent=4)
