# -*- encoding: utf-8 -*-

from datetime import datetime
from MySQL import MySQL

import uuid
import base64

class Service(object):

	def __init__(self):
		pass

	def __del__(self):
		pass

	def __getDB(self):
		return MySQL({
					'host'	: 'localhost',
					'port'	: 3306,
					'user'	: 'root',
					'passwd'	: '1q2w3e',
					'db'		: 'videos'})
	
	def getUserId(self,userKey):
		#db = self.__getDB()
		return 'aaaabbbbccccddddeeee04b6ada88888'

	def generateId(self):
		return str(uuid.uuid4()).replace('-','')


	def generateVideoId(self, data):
		userId = self.getUserId(data['UserKey'])
		db = self.__getDB()
		newId = self.generateId()
		
		result = db.save("""INSERT INTO `upload` (`id`, `owner_id`, `length`, `saved`, `update_time`) VALUES (%s,%s,%s,%s,%s)"""
					, (newId, userId, data['Length'], 0L, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
		db.end()
		return newId

	def upload_progress(self, data):
		userId = self.getUserId(data['UserKey'])
		db = self.__getDB()

		uploadSession = db.get("SELECT * FROM `upload` WHERE `id`=%s and `owner_id` = %s",(data['VID'], userId))
		if uploadSession == False:
			raise Exception("Upload session don't exists.")
		length = uploadSession['length']
		saved = uploadSession['saved']

		return length,saved

	def upload(self, data):
		userId = self.getUserId(data['UserKey'])
		db = self.__getDB()

		uploadSession = db.get("SELECT * FROM `upload` WHERE `id`=%s and `owner_id` = %s",(data['VID'], userId))

		if uploadSession == False:
			raise Exception("Upload session don't exists.")

		bindata = base64.b64decode(data['Data'])
		offset = data['Offset']
		length = uploadSession['length']
		saved = uploadSession['saved'] + len(bindata)

		if len(bindata) != data['Size']:
			raise Exception("Upload data and size don't match.")

		if length > 0 and saved > length:
			raise Exception("Upload data over alloc length.")

		if length > 0 and offset != uploadSession['saved']:
			raise Exception("Upload data don't sync.")

		if db.update("UPDATE `upload` SET `saved` = %s WHERE `id` = %s", (saved, data['VID'])) != 1:
			raise Exception("Write database error.")

		db.end()

		f = open(data['VID'], 'ab')
		f.write(bindata)
		f.close()

		return length,saved
