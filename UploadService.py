#coding=utf-8
#-*- encoding: utf-8 -*-

from MySQL import MySQL
from random import randint

import os
import hashlib
import base64

import Config
import Utils
import UserService



__uploadDirectory = Config.get('Server','Upload')
# auto create directory
if not os.path.exists(__uploadDirectory):
	os.makedirs(__uploadDirectory)



def upload_id(data):
	"""
	分配上传ID
	方法：
		upload_id
	参数：
		UserKey[string] –用户登录后的会话ID。
		Length[long] –视频字节数，单位BYTES。
	返回值：
		UploadId[string] – 分配的视频ID
		Length[long] – 视频字节数，单位BYTES。
	"""
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()

	newId = Utils.UUID()
	
	result = db.save("INSERT INTO `upload` (`id`, `owner_id`, `length`, `saved`, `update_time`) VALUES (%s,%s,%s,0,now())" , (newId, userId, long(data['Length'])))
	db.end()

	return newId


def upload_progress(data):
	"""
	获取视频上传进度
	方法：
		upload_progress
	参数：
		UserKey[string] –用户登录后的会话ID。
		UploadId[string] – 分配的视频ID
	返回值：
		Length[long] – 视频字节数，单位BYTES。
		Saved[long] – 上传字节数，单位BYTES。
	"""
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()

	uploadSession = db.get("SELECT * FROM `upload` WHERE `id`=%s and `owner_id` = %s",(data['UploadId'], userId))
	if uploadSession == False:
		raise Exception("上传任务不存在或已过期！")

	return ({'length':long(uploadSession['length']), 'saved':long(uploadSession['saved'])})


def upload_data(data):
	"""
	上传内容
	方法：
		upload_data
	参数：
		UserKey[string] –用户登录后的会话ID。
		UploadId[string] – 分配的视频ID
		Offset[long] – 视频文件偏移，单位BYTES。
		Data[string] – 数据包，经Base64编码后的数据包。
		Size[long] – 数据包包含数据大小（Base64编码前）。
	返回值：
		Length[long] – 视频字节数，单位BYTES。
		Saved[long] – 上传字节数，单位BYTES。
	"""
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()

	uploadSession = db.get("SELECT * FROM `upload` WHERE `id` = %s and `owner_id` = %s",(data['UploadId'], userId))

	if uploadSession == False:
		raise Exception("上传任务不存在或已过期！")

	bindata = base64.b64decode(data['Data'])
	offset = data['Offset']
	length = uploadSession['length']
	saved = uploadSession['saved'] + len(bindata)

	if len(bindata) != data['Size']:
		raise Exception("上传数据大小与提供的'Size'不匹配！")

	if length > 0 and saved > length:
		raise Exception("上传数据溢出！")

	if length > 0 and offset != uploadSession['saved']:
		raise Exception("上传数据不同步！")


	if db.update("UPDATE `upload` SET `saved` = %s, `update_time` = now() WHERE `id` = %s and `owner_id` = %s", (saved, data['UploadId'], userId)) != 1:
		raise Exception("同步数据库失败！")
	db.end()


	fileName = "%s/%s" % (__uploadDirectory, data['UploadId'])

	f = open(fileName, 'ab')
	f.write(bindata)
	f.close()

	return ({'length':long(length), 'saved':long(saved)})

