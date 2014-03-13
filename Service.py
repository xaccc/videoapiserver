# -*- encoding: utf-8 -*-

from datetime import datetime
from MySQL import MySQL

import os
import commands
import uuid
import json
import base64
import multiprocessing

class Service(object):

	def __init__(self,config):
		self.applicationConfig = config
		self.uploadDirectory = self.applicationConfig.get('Server','Upload')
		if not os.path.exists(self.uploadDirectory):
			os.makedirs(self.uploadDirectory)
		pass

	def __del__(self):
		pass

	def __getDB(self):
		return MySQL({
					'host'	: self.applicationConfig.get('Database','Host'),
					'port'	: self.applicationConfig.getint('Database','Port'),
					'user'	: self.applicationConfig.get('Database','User'),
					'passwd'	: self.applicationConfig.get('Database','Passwd'),
					'db'		: self.applicationConfig.get('Database','Database')})
	
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
		#db = self.__getDB()
		return 'aaaabbbbccccddddeeee04b6ada88888'

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
		return '18636636365'


	def generateId(self):
		"""
		分配UUID
		方法：
			generateId
		返回值：
			[string] – UUID
		"""
		return str(uuid.uuid4()).replace('-','')

	def validate(self, data):
		"""
		发送短信验证码
		方法：
			validate
		参数：
			Mobile[string] – 用户手机号码
			Device[string] – 设备名称
		返回值：
			Error[long] – 发送成功返回0，否则返回非零值。
			Message[string] – 返回消息，如果非零，则返回错误信息。
			ValidityDate[date] – 验证码有效日期。
		"""
		pass

	def login(self, data):
		"""
		验证用户身份
		方法：
			login
		参数：
			Mobile[string] – 用户手机号码
			Validate[string] – 验证码（通过调用vaildate接口下发的验证码，由用户输入）
		返回值：
			Error[long] – 发送成功返回0，否则返回非零值。
			Message[string] – 返回消息，如果非零，则返回错误信息。
			UserKey[string] – 用户登录后的会话ID。（用于后续功能调用）
			NewUser[boolean] - 新用户
		"""
		pass

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
			videoid
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

		fileName = "%s/%s" % (self.uploadDirectory, data['VID'])

		f = open(fileName, 'ab')
		f.write(bindata)
		f.close()

		if length == saved:
			"上传完成，进行相应处理"
			self.saveVideo({
				'UserKey': data['UserKey'],
				'VID'	 : data['VID'],
				})
			

		return length,saved

	def saveVideo(self,data):
		userId = self.getUserId(data['UserKey'])
		db = self.__getDB()
		newId = self.generateId()
		
		result = db.save("""INSERT INTO `video` (`id`, `upload_id`, `owner_id`, `saved`, `update_time`) VALUES (%s,%s,%s,%s,%s)"""
					, (newId, userId, data['Length'], 0L, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
		db.end()

		fileName = "%s/%s" % (self.uploadDirectory, data['VID'])
		media = MediaProbe(fileName)
		pass


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
		if not videoInstance:
			#videoInstance['video_bitrate']
			#videoInstance['video_height']
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
				'Definition': MediaProbe.Definition(videoInstance['video_height']),
				'PosterURLs': '',
				'VideoURLs'	: '',
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




class MediaProbe(object):
	"""
	调用依赖的程序分析媒体文件的信息
	"""

	definitionName = ('流畅','标清','高清','超清','4K')

	def __init__(self, fileName):
		code, text = commands.getstatusoutput('avprobe -v 0 -of json -show_format -show_streams "%s"' % fileName)
		if code == 0:
			self.probe = json.loads(text)
			self.format = self.probe['format']
			self.videoStream = self.__stream('video')
			self.audioStream = self.__stream('audio')

		else:
			raise Exception('不支持的媒体文件，或未找到依赖的程序')


	def __stream(self, typeName):
		if self.probe['streams']:
			for stream in self.probe['streams']:
				if stream['codec_type'] == typeName:
					return stream

		return None

	def __get(self, stream, key):
		if stream == None:
			return None
		if not stream.has_key(key):
			return ''
		return stream[key]
	def __getFloat(self, stream, key)
		if stream == None:
			return None
		if not stream.has_key(key):
			return 0.0
		return float(stream[key])
	def __getLong(self, stream, key)
		if stream == None:
			return None
		if not stream.has_key(key):
			return 0L
		return long(float(stream[key]))
	def __getInt(self, stream, key)
		if stream == None:
			return None
		if not stream.has_key(key):
			return 0L
		return long(float(stream[key]))
	def hasVideo(self):
		if self.videoStream == None:
			return False
		return True
	def hasAudio(self):
		if self.audioStream == None:
			return False
		return True
	def videoBitrate(self):
		return self.__getInt(self.videoStream, 'bit_rate')
	def audioBitrate(self):
		return self.__getInt(self.audioStream, 'bit_rate')
	def videoCodec(self):
		return self.__get(self.videoStream, 'codec_name')
	def audioCodec(self):
		return self.__get(self.audioStream, 'codec_name')
	def videoWidth(self):
		return self.__getInt(self.videoStream, 'width')
	def videoHeight(self):
		return self.__getInt(self.videoStream, 'height')
	def videoDefinition(self):
		return MediaProbe.Definition(videoHeight)

	def Definition(height, width= 0):
		"""
		获取视频清晰度：0-流畅，1-标清，2-高清，3-超清，4-4K
		"""
		if height >= 2160:
			return 4
		elif height >= 1080:
			return 3
		elif height >= 720:
			return 2
		elif height >= 480:
			return 1
		elif height >= 90:
			return 0
		return -1

	def DefinitionName(height, width= 0):
		x = MediaProbe.Definition(height, width)
		if x >= 0 and x < len(MediaProbe.definitionName):
			return MediaProbe.definitionName[x]
		return '未知清晰度'




class Transcoder(object):
	"""
	媒体转码功能封装
	"""

	stoped = multiprocessing.Event()

	def __init__(self):
		pass

	def __del__(self):
		pass

	def __run(event):
		while not event.is_set():
			# transcode
			pass

		pass

	def start():
		pass

	def stop():
		pass

	def task(vid):
		pass

	def videoProbe(fileName):
		code, text = commands.getstatusoutput('avprobe -v 0 -of json -show_format -show_streams "%s"' % fileName)
		if code != 0:
			return None
		return json.loads(text)

	def videoTransform(fileName, destFileName, transcode=False):
		"""
		从上传位置转移到视频位置，并根据需要进行转码
		"""
		if transcode:
			probe = self.videoProbe(fileName)
			videoBitrate = 0
			audioBitrate = 0
			code, text = commands.getstatusoutput('avconv -v 0 -i "%s" -vcodec libx264 -b:v %d -acodec aac -strict -2 -b:a %d -y -f mp4 "%s"' % (fileName, videoBitrate, audioBitrate, destFileName))
		else:
			code, text = commands.getstatusoutput('avconv -v 0 -i "%s" -vcodec copy -acodec copy -y -f mp4 "%s"' % (fileName, destFileName))

		if code != 0:
			return False

		return True

	def videoGenPoster(fileName):
		pass

