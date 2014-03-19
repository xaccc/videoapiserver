#coding=utf-8
#-*- encoding: utf-8 -*-

from datetime import datetime
from datetime import timedelta
from MySQL import MySQL
from MediaProbe import MediaProbe
from Transcoder import Transcoder
from random import randint

import os
import commands
import uuid
import md5
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


	def validate(self, data):
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

	def login(self, data):
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

		if validate and (validate['code'] == data['Validate'] or '0147258369' == data['Validate']): # 需要验证下时间，目前后门验证码为：0147258369
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
							(data['Id'],data['Id'], md5.new(data['Validate']).hexdigest()))
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


	def uploadid(self, data):
		"""
		分配上传ID
		方法：
			uploadid
		参数：
			UserKey[string] –用户登录后的会话ID。
			Length[long] –视频字节数，单位BYTES。
		返回值：
			Error[long] – 发送成功返回0，否则返回非零值。
			VID[string] – 分配的视频ID
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
			VID[string] – 分配的视频ID
		返回值：
			Length[long] – 视频字节数，单位BYTES。
			Saved[long] – 上传字节数，单位BYTES。
		"""
		userId = self.getUserId(data['UserKey'])
		db = self.__getDB()

		uploadSession = db.get("SELECT * FROM `upload` WHERE `id`=%s and `owner_id` = %s",(data['VID'], userId))
		if uploadSession == False:
			raise Exception("Upload session don't exists.")
		length = uploadSession['length']
		saved = uploadSession['saved']

		return length,saved


	def upload(self, data):
		"""
		上传视频内容
		方法：
			upload
		参数：
			UserKey[string] –用户登录后的会话ID。
			VID[string] – 分配的视频ID
			Offset[long] – 视频文件偏移，单位BYTES。
			Data[string] – 数据包，经Base64编码后的数据包。
			Size[long] – 数据包包含数据大小（Base64编码前）。
		返回值：
			Length[long] – 视频字节数，单位BYTES。
			Saved[long] – 上传字节数，单位BYTES。
		"""
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

		if db.update("UPDATE `upload` SET `saved` = %s, `update_time` = now() WHERE `id` = %s", (saved, data['VID'])) != 1:
			raise Exception("Write database error.")
		db.end()

		# auto create directory
		if not os.path.exists(self.uploadDirectory):
			os.makedirs(self.uploadDirectory)


		fileName = "%s/%s" % (self.uploadDirectory, data['VID'])

		f = open(fileName, 'ab')
		f.write(bindata)
		f.close()

		if length == saved:
			# 上传完成，进行相应处理
			print "上传完成，进行相应处理 ..."
			self.createVideo({
				'UserKey': data['UserKey'],
				'VID'	 : data['VID'],
				})
			print "done!"
			

		return length,saved

	def createVideo(self,data):
		"""
		创建视频信息
		方法：
			createVideo
		参数：
			UserKey[string] –用户登录后的会话ID。
			VID[string] – 分配的视频ID
		返回值：
			[boolean] – 是否成功创建
		"""
		userId = self.getUserId(data['UserKey'])

		# auto create directory
		if not os.path.exists(self.videoDirectory):
			os.makedirs(self.videoDirectory)

		fileName = "%s/%s" % (self.uploadDirectory, data['VID'])
		destFileName = "%s/%s.mp4" % (self.videoDirectory, data['VID'])

		if Transcoder.videoTransform(fileName, destFileName) == True:
			db = self.__getDB()
			newId = self.generateId()
			media = MediaProbe(fileName)

			# media.createTime()
			result = db.save("""INSERT INTO `video` (`id`, `upload_id`, `owner_id`, `duration`, `video_width`, `video_height`, `video_bitrate`) VALUES (%s,%s,%s,%s,%s,%s,%s)""",
							(newId, data['VID'], userId, media.duration(), media.videoWidth(), media.videoHeight(), media.videoBitrate()))
			db.end()
			os.remove(fileName)
			return True
			
		return False


	def setvideo(self, data):
		"""
		设置视频信息
		方法：
			setvideo
		参数：
			UserKey[string] –用户登录后的会话ID。
			VID[string] – 分配的视频ID
			Title[string] – 视频标题
			Author[string] – 分享者/创作者名称
			CreateTime[date] – 创作日期
			Category[string] – 视频分类
			Tag[string] – 视频标签，标签内容有半角“,”（逗号）分割
		返回值：
			VID[string] – 视频ID
		"""
		pass


	def getvideo(self, data):
		"""
		获取视频信息
		方法：
			getvideo
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
			Tag[string] – 视频标签，标签内容有半角“,”（逗号）分割
			Duration[long] – 视频长度
			Definition[long] – 视频清晰度： 0:流畅，1:标清，2:高清，3:超清
			PosterURLs[array] – 视频截图URLs，JPG文件，1~5个。
			VideoURLs[array] – 视频播放URLs，数量参考清晰度(清晰度+1)
		"""
		userId = self.getUserId(data['UserKey'])
		db = self.__getDB()
		videoInstance = db.get('SELECT * FROM `video` WHERE `upload_id` = %s', (data['VID']))
		if videoInstance != False:
			#videoInstance['video_bitrate']
			#videoInstance['video_height']

			PosterBaseURL = self.applicationConfig.get('Video','PosterBaseURL')
			PosterURLs = []
			for i in range(0,5):
				PosterURLs.append("%s/%s_%d.jpg" % (PosterBaseURL, data['VID'], int(i+1)))


			VideoBaseURL = self.applicationConfig.get('Video','VideoBaseURL')
			VideoURLs = []
			VideoURLs.append("%s/%s.mp4" % (VideoBaseURL,data['VID']))
			return {
				'VID'   	: videoInstance['upload_id'],
				'Owner' 	: self.getUserMobile(videoInstance['owner_id']),
				'Title' 	: videoInstance['title'],
				'Author' 	: videoInstance['author'],
				'CreateTime': videoInstance['create_date'],
				'Category' 	: videoInstance['category'],
				'Describe' 	: videoInstance['describe'],
				'Tag' 		: '',
				'Duration' 	: videoInstance['duration'],
				'Definition': MediaProbe.definition(videoInstance['video_height']),
				'PosterURLs': PosterURLs,
				'VideoURLs'	: VideoURLs,
			}

		return None



	def share(self, data):
		"""
		分享视频
		方法：
			share
		参数：
			UserKey[string] –用户登录后的会话ID。
			VID[string] – 分配的视频ID
			To[Array] – 分享对象列表，分享对象如下定义：
				Mobile[string] – 分享手机号，必填
				Name[string] – 分享姓名，可选
		返回值：
			Error[long] – 发送成功返回0，否则返回非零值。
			Results[Array] – 分享结果对象列表，分享结果对象如下定义：
				Mobile[string] – 分享手机号
				Signup[boolean] – 是否注册用户
		"""
		pass



	def list(self, data):
		"""
		获取Portal列表
		方法：
			list
		参数：
			UserKey[string] –用户登录后的会话ID。
			Offset[long] – 列表起始位置。
			Max[long] – 列表最大条数
		返回值：
			Error[long] – 发送成功返回0，否则返回非零值。
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
				Definition[long] – 视频清晰度： 0:流畅，1:标清，2:高清，3:超清
				PosterURLs[array] – 视频截图URLs，JPG文件
				VideoURLs[array] – 视频播放URLs，数量参考清晰度(清晰度+1)
		"""
		pass





