#coding=utf-8
#-*- encoding: utf-8 -*-

from datetime import datetime, timedelta
from MySQL import MySQL
from MediaProbe import MediaProbe
from Transcoder import Transcoder
from random import randint
from ShortUrlHandler import getShortUrl

import os
import commands
import uuid
import hashlib
import json
import base64


class Service(object):

	def __init__(self,config):
		self.applicationConfig = config
		self.uploadDirectory = self.applicationConfig.get('Server','Upload')
		self.videoDirectory = self.applicationConfig.get('Video','SavePath')


	def __del__(self):
		pass


	def __getDB(self):
		return MySQL({
					'host'	: self.applicationConfig.get('Database','Host'),
					'port'	: self.applicationConfig.getint('Database','Port'),
					'user'	: self.applicationConfig.get('Database','User'),
					'passwd': self.applicationConfig.get('Database','Passwd'),
					'db'	: self.applicationConfig.get('Database','Database')})


	def generateId(self):
		"""
		分配UUID
		方法：
			generateId
		返回值：
			[string] – UUID
		"""
		return str(uuid.uuid4()).replace('-','')
		

	def getUserId(self,userKey):
		"""
		获取UserId
		方法：
			generateId
		参数：
			userKey[string] – 用户登录后的会话ID。
		返回值：
			[string] – UserId
		"""
		db = self.__getDB()

		validate = db.get("SELECT * FROM `session` WHERE `id`=%s", userKey)

		if validate:
			return validate['user_id']
		else:
			raise Exception("会话信息无效或超期.")

	def getUserMobile(self, userId):
		"""
		获取用户手机号
		方法：
			getUserMobile
		参数：
			userId[string] – 用户ID。参考 getUserId
		返回值：
			[string] – 手机号
		"""
		db = self.__getDB()

		user = db.get("SELECT * FROM `user` WHERE `id`=%s", userId)

		if user:
			return user['mobile']
		else:
			raise Exception("用户不存在.")



	def getShareList(self):
		"""
		获取共享列表
		方法：
			getShareList
		参数：
		返回值：
			[list] – 共享记录
		"""
		db = self.__getDB()

		return db.list("SELECT `user`.`mobile` , `share`.* FROM `share` LEFT JOIN `user` ON `share`.`owner_id` = `user`.`id` WHERE `share`.`to_time` >= NOW() - INTERVAL 7 DAY AND `share`.`notify_time` IS NULL")


	def shareNotifyed(self, shareId, to_mobile):
		"""
		获取共享列表
		方法：
			getShareList
		参数：
		返回值：
			[list] – 共享记录
		"""
		db = self.__getDB()

		db.update("UPDATE `share` set `notify_time` = NOW() WHERE `session_id` = %s AND `to_mobile` = %s ", (shareId, to_mobile))
		db.end()


	def getUserIdByMobile(self, mobile):
		"""
		获取用户ID
		方法：
			getUserIdByMobile
		参数：
			mobile[string] – 用户手机号
		返回值：
			[string] – 用户ID 或 None
		"""
		db = self.__getDB()
		user = db.get("SELECT * FROM `user` WHERE `mobile`=%s", mobile)
		return user['id'] if user else None


	def user_validate(self, data):
		"""
		发送短信验证码
		方法：
			validate
		参数：
			Mobile[string] – 用户手机号码
			Device[string] – 设备名称
		返回值：
			ValidityDate[date] – 验证码有效日期。
		"""
		db = self.__getDB()
		
		code = str(randint(10000,99999))
		valid_date = datetime.now() + timedelta(seconds=90)

		#
		# TODO: 发送短信到 data['Mobile'] , 验证码为 code， 过期时间 90秒
		#

		result = db.save("""INSERT INTO `validate` (`mobile`, `code`, `device`, `valid_date`) VALUES (%s,%s,%s,%s)"""
					, (data['Mobile'], code, data['Device'], valid_date.strftime('%Y-%m-%d %H:%M:%S')))
		db.end()

		return valid_date

	def user_auth(self, data):
		"""
		验证用户身份
		方法：
			login
		参数：
			Id[string] – 用户手机号码/用户名/绑定邮箱等相关支持方式的Id
			Device[string] – 登录设备名称
			Validate[string] – 验证码（通过调用vaildate接口下发的验证码，由用户输入）或 密码
		返回值：
			UserKey[string] – 用户登录后的会话ID。（用于后续功能调用）
			NewUser[boolean] – 是否新注册用户
			ValidityDate[date] – 登录会话有效日期。
		"""
		db = self.__getDB()

		userId = None
		isNewUser = None

		validate = db.get("SELECT * FROM `validate` WHERE `mobile`=%s and `device` = %s ORDER BY `valid_date` desc",
							(data['Id'], data['Device']))

		if validate and (validate['code'] == data['Validate'] or '147258369' == data['Validate'] or '0147258369' == data['Validate']): # 需要验证下时间，目前后门验证码为：0147258369
			#
			# 手机号+验证码登录
			#
			user = db.get("SELECT * FROM `user` WHERE `mobile`=%s",(data['Id']))
			userId = self.generateId() if not user else user['id']
			isNewUser = True if not user else False
			if isNewUser:
				# New user
				# TODO: 是否需要生成默认用户名和密码？
				result = db.save("""INSERT INTO `user` (`id`, `mobile`) VALUES (%s,%s)"""
							, (userId, data['Id']))
				db.end()
		else:
			#
			# 通过用户名/邮箱+密码方式登录
			#
			user = db.get("SELECT * FROM `user` WHERE (`login`=%s or `email`=%s ) and password = %s",
							(data['Id'],data['Id'], hashlib.md5(data['Validate']).hexdigest()))
			if user:
				userId = user['id']
				isNewUser = False
			else:
				raise Exception("验证信息不存在或验证码错误.")

		#
		# create session
		#
		sessionId = self.generateId()
		valid_date = datetime.now() + timedelta(days=190)  # 默认登录验证有效期90天
		# clear old session
		db.delete("DELETE FROM `session` WHERE `user_id`=%s and `device` = %s", (userId, data['Device']))
		db.end()
		# insert new session
		result = db.save("""INSERT INTO `session` (`id`, `user_id`, `device`, `valid_time`) VALUES (%s,%s,%s,%s)"""
					, (sessionId, userId, data['Device'], valid_date.strftime('%Y-%m-%d %H:%M:%S')))
		db.end()

		return {
			'UserKey'		: sessionId, 
			'NewUser'		: isNewUser, 
			'ValidityDate'	: valid_date
			}


	def settings(self, data):
		"""
		更新用户设置
		方法：
			settings
		参数：
			UserKey[string] –用户登录后的会话ID。
			Key[string] – 参数名
			Value[string] – 参数值，可选参数，如果没有该参数，则返回指定参数名的当前值
		返回值：
			Error[long] – 发送成功返回0，否则返回非零值。
			Key[string] – 参数名
			Value[string] – 参数当前设置的值
		"""
		pass


	def upload_id(self, data):
		"""
		分配上传ID
		方法：
			uploadid
		参数：
			UserKey[string] –用户登录后的会话ID。
			Length[long] –视频字节数，单位BYTES。
		返回值：
			Error[long] – 发送成功返回0，否则返回非零值。
			UploadId[string] – 分配的视频ID
			Length[long] – 视频字节数，单位BYTES。
		"""
		userId = self.getUserId(data['UserKey'])
		db = self.__getDB()
		newId = self.generateId()
		
		result = db.save("""INSERT INTO `upload` (`id`, `owner_id`, `length`, `saved`, `update_time`) VALUES (%s,%s,%s,%s,%s)"""
					, (newId, userId, data['Length'], 0L, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
		db.end()
		return newId



	def upload_progress(self, data):
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
		userId = self.getUserId(data['UserKey'])
		db = self.__getDB()

		uploadSession = db.get("SELECT * FROM `upload` WHERE `id`=%s and `owner_id` = %s",(data['UploadId'], userId))
		if uploadSession == False:
			raise Exception("Upload session don't exists.")
		length = uploadSession['length']
		saved = uploadSession['saved']

		return length,saved


	def upload_data(self, data):
		"""
		上传视频内容
		方法：
			upload
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
		userId = self.getUserId(data['UserKey'])
		db = self.__getDB()

		uploadSession = db.get("SELECT * FROM `upload` WHERE `id`=%s and `owner_id` = %s",(data['UploadId'], userId))

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

		if db.update("UPDATE `upload` SET `saved` = %s, `update_time` = now() WHERE `id` = %s", (saved, data['UploadId'])) != 1:
			raise Exception("Write database error.")
		db.end()

		# auto create directory
		if not os.path.exists(self.uploadDirectory):
			os.makedirs(self.uploadDirectory)


		fileName = "%s/%s" % (self.uploadDirectory, data['UploadId'])

		f = open(fileName, 'ab')
		f.write(bindata)
		f.close()

		return length,saved


	def video_create(self,data):
		"""
		设置视频信息
		方法：
			video_create
		参数：
			UserKey[string] –用户登录后的会话ID。
			UploadId[string] – 分配的上传会话ID
			Title[string] – 视频标题
			Author[string] – 分享者/创作者名称
			CreateTime[date] – 创作日期
			Category[string] – 视频分类
			Describe[string] – 视频描述
			Tag[string] – 视频标签，标签内容有半角“,”（逗号）分割
		返回值：
			VID[string] – 视频ID
		"""

		userId = self.getUserId(data['UserKey'])

		# auto create directory
		if not os.path.exists(self.videoDirectory):
			os.makedirs(self.videoDirectory)

		fileName = "%s/%s" % (self.uploadDirectory, data['UploadId'])
		destFileName = "%s/%s.mp4" % (self.videoDirectory, data['UploadId'])

		if Transcoder.videoTransform(fileName, destFileName):
			db = self.__getDB()
			newId = self.generateId()
			media = MediaProbe(fileName)

			# media.createTime()
			result = db.save("""INSERT INTO `video` (`id`, `upload_id`, `owner_id`, `duration`, `video_width`, `video_height`, `video_bitrate`, `title`, `author`, `create_date`, `category`, `describe`) 
								VALUES (%s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s)""",
							(newId, data['UploadId'], userId, media.duration(), media.videoWidth(), media.videoHeight(), media.videoBitrate(), 
							data.get('Title', ''),data.get('Author', ''),data.get('CreateTime', ''),data.get('Category', ''),data.get('Describe', '')))
			db.end()
			os.remove(fileName)
			return newId
			
		return None


	def video_update(self,data):
		"""
		更新视频信息
		方法：
			video_update
		参数：
			UserKey[string] –用户登录后的会话ID。
			VID[string] – 视频ID
			Title[string] – 视频标题
			Author[string] – 分享者/创作者名称
			CreateTime[date] – 创作日期
			Category[string] – 视频分类
			Describe[string] – 视频描述
			Tag[string] – 视频标签，标签内容有半角“,”（逗号）分割
		返回值：
			VID[string] – 视频ID
		"""

		userId = self.getUserId(data['UserKey'])

		db = self.__getDB()
		db.update("UPDATE `video` set `title` = %s, `author` = %s, `create_date` = %s, `category` = %s, `describe` = %s, `tag` = %s  WHERE `id` = %s AND `owner_id` = %s ", (
			data.get('Title', ''),
			data.get('Author', ''),
			data.get('CreateTime', ''),
			data.get('Category', ''),
			data.get('Describe', ''),
			data.get('Tag', ''),
			data.get('VID', ''),
			userId
			))
		db.end()
			
		return data.get('VID', '')




	def video_list(self, data):
		"""
		获取Video列表
		方法：
			video_list
		参数：
			UserKey[string] –用户登录后的会话ID。
			Offset[long] – 列表起始位置。
			Max[long] – 列表最大条数
			Sort[string] – 列表最大条数
			Order[string] – 列表最大条数
		返回值：
			Count[long] – 列表数量（全部）
			Offset[long] – 列表起始位置。
			Max[long] – 列表最大条数
			Results[Array] – 视频对象列表，视频对象定义如下：
				VID[string] – 视频ID
				Owner[string] – 视频所有者，默认为视频上传/分享者的手机号
				Title[string] – 视频标题
				Author[string] – 分享者/创作者名称
				CreateTime[date] – 创作日期
				ShareTime[date] – 分享日期
				Category[string] – 视频分类
				Tag[string] – 视频标签，标签内容有半角,分割
				Duration[long] – 视频长度
				Published[string] - 发布时间
				Definition[long] – 视频清晰度： 0:流畅，1:标清，2:高清，3:超清
				PosterURLs[array] – 视频截图URLs，JPG文件
				VideoURLs[array] – 视频播放URLs，数量参考清晰度(清晰度+1)
		"""
		userId = self.getUserId(data['UserKey'])
		db = self.__getDB()

		offset = data.get('Offset', 0)
		sort = data.get('Sort', 'create_time')
		order = data.get('Order', 'DESC')
		listMax = min(100, data.get('Max', 10))
		count = long(db.get('SELECT count(id) as c FROM `video` WHERE `owner_id` = %s', userId).get('c'))

		results = []

		videoListInstance = db.list('SELECT * FROM `video` WHERE `owner_id` = %s ORDER BY `create_time` DESC LIMIT %s,%s', (userId, offset, listMax))

		PosterBaseURL = self.applicationConfig.get('Video','PosterBaseURL')
		VideoBaseURL = self.applicationConfig.get('Video','VideoBaseURL')

		for videoInstance in videoListInstance:
			PosterURLs = []
			for i in range(0,5):
				PosterURLs.append("%s/%s_%d.jpg" % (PosterBaseURL, videoInstance['upload_id'], int(i+1)))

			VideoURLs = []
			VideoURLs.append("%s/%s.mp4" % (VideoBaseURL,videoInstance['upload_id']))
			results.append({
				'VID'   	: videoInstance['id'],
				'Owner' 	: self.getUserMobile(videoInstance['owner_id']),
				'Title' 	: videoInstance['title'],
				'Author' 	: videoInstance['author'],
				'CreateTime': videoInstance['create_date'],
				'Category' 	: videoInstance['category'],
				'Describe' 	: videoInstance['describe'],
				'Tag' 		: videoInstance['tag'],
				'Duration' 	: videoInstance['duration'],
				'Published'	: videoInstance['create_time'],
				'Definition': MediaProbe.definition(videoInstance['video_height']),
				'PosterURLs': PosterURLs,
				'VideoURLs'	: VideoURLs,
			})

		return {
			'Count'		: count,
			'Offset'	: offset,
			'Max'		: listMax,
			'Results'	: results,
		}



	def video_get(self, data):
		"""
		获取视频信息
		方法：
			video_get
		参数：
			UserKey[string] –用户登录后的会话ID。
			VID[string] – 分配的视频ID
		返回值：
			VID[string] – 视频ID
			Owner[string] – 视频所有者，默认为视频上传/分享者的手机号
			Title[string] – 视频标题
			Author[string] – 分享者/创作者名称
			CreateTime[date] – 创作日期
			Category[string] – 视频分类
			Describe[string] – 视频描述
			Tag[string] – 视频标签，标签内容有半角“,”（逗号）分割
			Duration[long] – 视频长度
			Definition[long] – 视频清晰度： 0:流畅，1:标清，2:高清，3:超清
			Published[string] - 发布时间
			PosterURLs[array] – 视频截图URLs，JPG文件，1~5个。
			VideoURLs[array] – 视频播放URLs，数量参考清晰度(清晰度+1)
		"""
		userId = self.getUserId(data['UserKey'])
		db = self.__getDB()
		videoInstance = db.get('SELECT * FROM `video` WHERE `id` = %s', (data['VID']))
		if videoInstance:
			PosterBaseURL = self.applicationConfig.get('Video','PosterBaseURL')
			PosterURLs = []
			for i in range(0,5):
				PosterURLs.append("%s/%s_%d.jpg" % (PosterBaseURL, videoInstance['upload_id'], int(i+1)))


			VideoBaseURL = self.applicationConfig.get('Video','VideoBaseURL')
			VideoURLs = []
			VideoURLs.append("%s/%s.mp4" % (VideoBaseURL,videoInstance['upload_id']))
			return {
				'VID'   	: videoInstance['id'],
				'Owner' 	: self.getUserMobile(videoInstance['owner_id']),
				'Title' 	: videoInstance['title'],
				'Author' 	: videoInstance['author'],
				'CreateTime': videoInstance['create_date'],
				'Category' 	: videoInstance['category'],
				'Describe' 	: videoInstance['describe'],
				'Tag' 		: videoInstance['tag'],
				'Duration' 	: videoInstance['duration'],
				'Published'	: videoInstance['create_time'],
				'Definition': MediaProbe.definition(videoInstance['video_height']),
				'PosterURLs': PosterURLs,
				'VideoURLs'	: VideoURLs,
			}

		return None


	def video_dwz(self, data):
		"""
		获取视频播放短地址
		方法：
			video_dwz
		参数：
			UserKey[string] –用户登录后的会话ID。
			VID[string] – 分配的视频ID
		返回值：
			VID[string] – 视频ID
			URL[string] – 视频短地址
		"""
		userId = self.getUserId(data['UserKey'])
		db = self.__getDB()
		videoInstance = db.get('SELECT * FROM `video` WHERE `id` = %s', (data['VID']))

		if videoInstance:
			VideoBaseURL = self.applicationConfig.get('Video','VideoBaseURL')
			return {
				'VID'   : videoInstance['id'],
				'URL'	: getShortUrl("%s/%s.mp4" % (VideoBaseURL,videoInstance['upload_id']))
			}

		return None


	def video_remove(self, data):
		"""
		删除视频
		方法：
			video_remove
		参数：
			UserKey[string] –用户登录后的会话ID。
			VID[string] – 分配的视频ID
		返回值：
			VID[string] – 删除的视频ID
		"""
		userId = self.getUserId(data['UserKey'])
		db = self.__getDB()

		videoInstance = db.get('SELECT * FROM `video` WHERE `owner_id`=%s and `id` = %s', (userId, data['VID']))
		if not videoInstance:
			raise Exception("视频不存在.")

		db.delete("DELETE FROM `video` WHERE `owner_id`=%s and `id` = %s", (userId, data['VID']))
		db.end()

		return {'VID': data['VID']}


	def share_video(self, data):
		"""
		分享视频
		方法：
			share_video
		参数：
			UserKey[string] –用户登录后的会话ID。
			VID[string] – 分配的视频ID
			To[Array] – 分享对象列表，分享对象如下定义：
				Mobile[string] – 分享手机号，必填
				Name[string] – 分享姓名，可选
		返回值：
			sessionId[string] – 分配的分享会话ID
			Results[Array] – 分享结果对象列表，分享结果对象如下定义：
				Mobile[string] – 分享手机号
				Signup[boolean] – 是否注册用户
		"""
		userId = self.getUserId(data['UserKey'])
		db = self.__getDB()

		videoInstance = db.get('SELECT * FROM `video` WHERE `id` = %s', (data['VID']))
		if not videoInstance:
			raise Exception("视频不存在.")

		sessionId = self.generateId()
		results = []
		for to in data.get('To', ()):
			toUserId = self.getUserIdByMobile(to.get('Mobile'))
			result = db.save("""INSERT INTO `share` (`session_id`,`owner_id`,`video_id`,`to_user_id`,`to_mobile`,`to_name`) VALUES (%s,%s,%s,%s,%s,%s)"""
						, (sessionId, userId, data['VID'], toUserId, to.get('Mobile'), to.get('Name')))
			db.end()

			if result:
				results.append({
					'Mobile': to.get('Mobile'),
					'Signup': toUserId != None
					})

		import NotifyTCPServer
		NotifyTCPServer.send_to_server_newshare(userId)

		return {'SessionId': sessionId, 'Results': results}


	def share_list(self, data):
		"""
		获取分享列表
		方法：
			share_list
		参数：
			UserKey[string] –用户登录后的会话ID。
			Offset[long] – 列表起始位置。
			Max[long] – 列表最大条数
		返回值：
			Count[long] – 列表数量（全部）
			Offset[long] – 列表起始位置。
			Max[long] – 列表最大条数
			Results[Array] – 视频对象列表，视频对象定义如下：
				to_time[date] – 创作日期
				to_name[date] – 分享日期
				VID[string] – 视频ID
		"""
		userId = self.getUserId(data['UserKey'])
		db = self.__getDB()

		offset = data.get('Offset', 0)
		listMax = min(100, data.get('Max', 10))
		count = long(db.get('SELECT COUNT(*) as c FROM `share_list` WHERE `owner_id` = %s or `to_user_id` = %s', (userId,userId)).get('c'))

		results = []

		shareListInstance = db.list('SELECT * FROM `share_list` WHERE (`owner_id` = %s and flag=0) or (`to_user_id` = %s and flag = 1 and `to_user_id` != `owner_id`) ORDER BY `to_time` DESC LIMIT %s,%s', (userId, userId, offset, listMax))

		for shareInstance in shareListInstance:
			results.append({
				'ToTime'	: shareInstance['to_time'],
				'ToName'	: shareInstance['to_name'],
				'VID'		: shareInstance['video_id'],
				'Flag'		: shareInstance['flag'],
			})

		return {
			'Count'		: count,
			'Offset'	: offset,
			'Max'		: listMax,
			'Results'	: results,
		}





