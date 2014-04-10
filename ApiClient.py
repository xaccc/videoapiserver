#coding=utf-8
#-*- encoding: utf-8 -*-

import os
import sys
import json
import uuid
import urllib2
import base64

from ConfigParser import ConfigParser


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


	def validate(self,mobile,device):
		return self.__postJSON(baseURL + '/validate', {
				'Mobile'	: mobile,
				'Device'	: device,
				})


	def login(self,id,device,validate):
		result = self.__postJSON(baseURL + '/login', {
					'Id'		: id,
					'Device'	: device,
					'Validate'	: validate,
					})
		self.userKey = result['UserKey'] if result and result['UserKey'] else ''
		return result


	def uploadSession(self,length):
		return self.__postJSON(baseURL + '/uploadid', {
				'UserKey'	: self.userKey,
				'Length'	: length,
				})


	def uploadProgress(self,id):
		return self.__postJSON(baseURL + '/upload_progress', {
				'UserKey'	: self.userKey,
				'UploadId'	: id,
				})


	def upload(self,id, length, offset, bdata):
		return self.__postJSON(baseURL + '/upload', {
				'UserKey'	: self.userKey,
				'UploadId'	: id,
				'Length'	: length,
				'Offset'	: offset,
				'Size'		: len(bdata),
				'Data'		: base64.b64encode(bdata),
				})


	def createVideo(self,id):
		return self.__postJSON(baseURL + '/createvideo', {
				'UserKey'	: self.userKey,
				'UploadId'	: id,
				})


	def getVideo(self,id):
		return self.__postJSON(baseURL + '/getvideo', {
				'UserKey'	: self.userKey,
				'VID'		: id,
				})

	def shreaVideo(self, id, toList):
		return self.__postJSON(baseURL + '/sharevideo', {
				'UserKey'	: self.userKey,
				'VID'		: id,
				'To'		: toList
				})

	def listShareVideo(self, offset=0, listMax=10):
		return self.__postJSON(baseURL + '/listsharevideo', {
				'UserKey'	: self.userKey,
				'Offset'	: offset,
				'Max'		: listMax
				})



	def video_list(self, offset=0, listMax=10):
		return self.__postJSON(baseURL + '/video_list', {
				'UserKey'	: self.userKey,
				'Offset'	: offset,
				'Max'		: listMax
				})





applicationConfig = ConfigParser()
applicationConfig.read('Config.ini')
baseURL = applicationConfig.get('Test', 'baseURL')
