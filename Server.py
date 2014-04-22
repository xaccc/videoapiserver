#coding=utf-8
#-*- encoding: utf-8 -*-


from datetime import date,datetime,timedelta
from urlparse import urljoin,urlsplit
from ConfigParser import ConfigParser

from Downloader import Download
from Service import Service
from ShortUrlHandler import ShortUrlHandler, getShortUrl, getUrl

import os,logging
import uuid, hashlib, json
import time, signal, multiprocessing
import httplib, tornado.web, tornado.ioloop, tornado.httpserver
import dateutil, dateutil.tz, dateutil.parser
import logging

logging.basicConfig(filename = os.path.join(os.getcwd(), 'server.log'), level = logging.DEBUG)


class MyJSONEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime):
			return obj.replace(tzinfo=dateutil.tz.tzlocal()).strftime('%Y-%m-%dT%H:%M:%SZ%z')
		elif isinstance(obj, date):
			return obj.replace(tzinfo=dateutil.tz.tzlocal()).strftime('%Y-%m-%d')
		else:
			return json.JSONEncoder.default(self, obj)


class MainHandler(tornado.web.RequestHandler):
	
	def initialize(self, service):
		self.service = service
		self.urlmap = {
			'validate'			: self.user_validate,
			'userkey'			: self.user_id,
			'login'				: self.user_auth,
			'settings'			: self.settings,
			'uploadid'			: self.upload_id,
			'upload'			: self.upload_data,
			'createvideo'		: self.video_create,
			'getvideo'			: self.video_get,
			'sharevideo'		: self.share_video,
			'listsharevideo'	: self.share_list,
			'publishvideo'		: self.publishvideo,

			# 身份认证接口
			'user_validate'		: self.user_validate,
			'user_auth'			: self.user_auth,
			'user_id'			: self.user_id,

			# 上传接口
			'upload_id'			: self.upload_id,
			'upload_progress'	: self.upload_progress,
			'upload_data'		: self.upload_data,

			# 视频相关接口
			'video_create'		: self.video_create,
			'video_list'		: self.video_list,
			'video_get'			: self.video_get,
			'video_update'		: self.video_update,
			'video_remove'		: self.video_remove,
			'video_dwz'			: self.video_dwz,
			'video_qrcode'		: self.video_qrcode,

			# 分享接口
			'share_video'		: self.share_video,
			'share_list'		: self.share_list,

			# 短地址接口
			'short_url'			: self.short_url,
			'short_url_get'		: self.short_url_get,
		}

	def post(self, api):
		if 'application/json' in self.request.headers['Content-Type']:
			self.urlmap.get(api, self.__responseDefault)(json.loads(self.request.body))
		else:
			raise tornado.web.HTTPError(400, '数据格式不支持')
	
	def __responseDefault(self,data):
		raise tornado.web.HTTPError(400, '功能不支持')

	def __reponseJSON(self, data):
		self.set_header('Content-Type', 'application/json')
		self.set_header('Server', 'VideoServer')
		self.write(json.dumps(data, cls=MyJSONEncoder))

	def __has_params(self, data, params):
		if not isinstance(data, dict):
			return False

		if isinstance(params, str):
			return data.has_key(params)

		for p in params:
			if not data.has_key(str(p)):
				return False
		return True

	def write_error(self, status_code, **kwargs):
		data = {'Error': status_code, 'Message': httplib.responses[status_code]}

		for item in kwargs['exc_info']:
			if isinstance(item,Exception):
				data['Message'] = str(item)

		self.__reponseJSON(data)


	#def _handle_request_exception(self, e):
	#	self.set_header('Content-Type', 'application/json')
	#	self.set_header('Server', 'Video API Server')
	#	self.write({'Error': -1, 'Message': str(e)})

	###########################################################################
	#
	# API 功能实现
	#
	###########################################################################
	
	def user_id(self, data):
		"""
		检验userKey是否有效
		方法：
			user_id
		参数：
			UserKey[string] – 用户登录后的会话ID
		返回值：
			UserId[String] – 用户ID
		"""

		if not self.__has_params(data, ('UserKey')):
			raise tornado.web.HTTPError(400, '参数Error')

		userId = self.service.getUserId(data['UserKey'])

		self.__reponseJSON({ 
			'Now'		: datetime.now(),
			'userId'	: userId
		})
	
	def user_validate(self, data):
		"""
		发送短信验证码
		方法：
			user_validate
		参数：
			Mobile[string] – 用户手机号码
			Device[string] – 设备名称
		返回值：
			ValidityDate[date] – 验证码有效日期。
		"""
		if not self.__has_params(data, ('Mobile', 'Device')):
			raise tornado.web.HTTPError(400, '参数Error')

		ValidityDate = self.service.user_validate(data)

		self.__reponseJSON({ 
			'Now'   		: datetime.now(),
			'ValidityDate'	: ValidityDate
		})


	def user_auth(self, data):
		"""
		验证用户身份
		方法：
			user_auth
		参数：
			Id[string] – 用户手机号码/用户名/绑定邮箱等相关支持方式的Id
			Device[string] – 登录设备名称
			Validate[string] – 验证码（通过调用vaildate接口下发的验证码，由用户输入）或 密码
		返回值：
			UserKey[string] – 用户登录后的会话ID。（用于后续功能调用）
			NewUser[boolean] – 是否新注册用户
			ValidityDate[date] – 登录会话有效日期。
		"""
		if not self.__has_params(data, ('Id', 'Device', 'Validate')):
			raise tornado.web.HTTPError(400, '参数Error')

		result = self.service.user_auth(data)
		if not result or not result['UserKey']:
			raise tornado.web.HTTPError(500, '验证码或用户名、密码错误!') 

		self.__reponseJSON({
			'Now'	  : datetime.now(),
			'UserKey' : result['UserKey'],
			'NewUser' : result['NewUser'],
			'ValidityDate' : result['ValidityDate']
			})
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
			Key[string] – 参数名
			Value[string] – 参数当前设置的值
		"""
		if not self.__has_params(data, ('UserKey', 'Key')):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON({
			'Now': datetime.now(),
			})
		pass



	def upload_id(self, data):
		"""
		分配视频ID
		方法：
			upload_id
		参数：
			UserKey[string] –用户登录后的会话ID。
			Length[long] –视频字节数，单位BYTES。
		返回值：
			UploadId[string] – 分配的上传会话ID
			Length[long] – 视频字节数，单位BYTES。
		"""
		if not self.__has_params(data, ('UserKey', 'Length')):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON({
			'Now'		: datetime.now(),
			'UploadId'	: self.service.upload_id(data),
			'Length'	: data['Length']
			})
		pass


	def upload_progress(self, data):
		"""
		获取视频上传进度
		方法：
			upload_progress
		参数：
			UserKey[string] –用户登录后的会话ID。
			UploadId[string] – 分配的上传会话ID
		返回值：
			Error[long] – 发送成功返回0，否则返回非零值。
			UploadId[string] – 分配的上传会话ID
			Saved[long] – 上传字节数，单位BYTES。
			Length[long] – 视频字节数，单位BYTES。
		"""
		if not self.__has_params(data, ('UserKey', 'UploadId')):
			raise tornado.web.HTTPError(400, '参数 Error')

		length, saved = self.service.upload_progress(data)
		self.__reponseJSON({
			'Now'   	: datetime.now(),
			'UploadId'	: data['UploadId'],
			'Length'	: length,
			'Saved' 	: saved,
			})
		pass

	def upload_data(self, data):
		"""
		上传视频内容
		方法：
			upload_data
		参数：
			UserKey[string] –用户登录后的会话ID。
			UploadId[string] – 分配的上传会话ID
			Offset[long] – 视频文件偏移，单位BYTES。
			Data[string] – 数据包，经Base64编码后的数据包。
			Size[long] – 数据包包含数据大小（Base64编码前）。
		返回值：
			Error[long] – 发送成功返回0，否则返回非零值。
			Saved[long] – 上传字节数，单位BYTES。
			Length[long] – 视频字节数，单位BYTES。
		"""
		if not self.__has_params(data, ('UserKey', 'UploadId', 'Offset', 'Data', 'Size')):
			raise tornado.web.HTTPError(400, '参数 Error')

		length, saved = self.service.upload_data(data)

		self.__reponseJSON({
			'Now'		: datetime.now(),
			'UploadId'	: data['UploadId'],
			'Length'	: length,
			'Saved'		: saved,
			})
		pass


	def video_create(self, data):
		"""
		创建视频信息
		方法：
			video_create
		参数：
			UserKey[string] –用户登录后的会话ID。
			UploadId[string] – 分配的上传会话ID
			Title[string] – 视频标题
			Author[string] – 分享者/创作者名称
			CreateTime[date] – 创作日期
			Category[string] – 视频分类
			Tag[string] – 视频标签，标签内容有半角“,”（逗号）分割
		返回值：
			VID[string] – 视频ID
		"""
		if not self.__has_params(data, ('UserKey', 'UploadId')):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON({
			'Now': datetime.now(),
			'VID': self.service.video_create(data)
			})
		pass



	def video_update(self, data):
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
			Tag[string] – 视频标签，标签内容有半角,分割
		返回值：
			VID[string] – 视频ID
		"""
		if not self.__has_params(data, ('UserKey', 'VID')):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON({
			'Now': datetime.now(),
			'VID': self.service.video_update(data)
			})
		pass


	def video_list(self, data):
		"""
		获取Video列表
		方法：
			video_list
		参数：
			UserKey[string] –用户登录后的会话ID。
			Offset[long] – 列表起始位置。
			Max[long] – 列表最大条数
			Sort[string] – 列表最大条数(可选)
			Order[string] – 列表最大条数(可选)
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
				Definition[long] – 视频清晰度： 0:流畅，1:标清，2:高清，3:超清
				PosterURLs[array] – 视频截图URLs，JPG文件
				VideoURLs[array] – 视频播放URLs，数量参考清晰度(清晰度+1)
		"""
		if not self.__has_params(data, ['UserKey']):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON(self.service.video_list(data))


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
			Tag[string] – 视频标签，标签内容有半角“,”（逗号）分割
			Duration[long] – 视频长度
			Definition[long] – 视频清晰度： 0:流畅，1:标清，2:高清，3:超清
			PosterURLs[array] – 视频截图URLs，JPG文件，1~5个。
			VideoURLs[array] – 视频播放URLs，数量参考清晰度(清晰度+1)
		"""
		if not self.__has_params(data, ('UserKey', 'VID')):
			raise tornado.web.HTTPError(400, '参数 Error')

		videoInstance = self.service.video_get(data)
		if videoInstance == None:
			raise tornado.web.HTTPError(404, '视频不存在')

		self.__reponseJSON({
			'Now'   	: datetime.now(),
			'VID'   	: data['VID'],
			'Owner' 	: videoInstance['Owner'],
			'Title' 	: videoInstance['Title'],
			'Author' 	: videoInstance['Author'],
			'CreateTime': videoInstance['CreateTime'],
			'Category' 	: videoInstance['Category'],
			'Tag' 		: videoInstance['Tag'],
			'Duration' 	: videoInstance['Duration'],
			'Definition': videoInstance['Definition'],
			'PosterURLs': videoInstance['PosterURLs'],
			'VideoURLs'	: videoInstance['VideoURLs'],
			})


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
		if not self.__has_params(data, ('UserKey', 'VID')):
			raise tornado.web.HTTPError(400, '参数 Error')

		videoInstance = self.service.video_dwz(data)
		if videoInstance == None:
			raise tornado.web.HTTPError(404, '视频不存在')

		self.__reponseJSON(videoInstance)


	def video_qrcode(self, data):
		"""
		获取视频播放短地址
		方法：
			video_qrcode
		参数：
			UserKey[string] –用户登录后的会话ID。
			VID[string] – 分配的视频ID
		返回值：
			VID[string] – 视频ID
			URL[string] – 视频短地址
		"""
		if not self.__has_params(data, ('UserKey', 'VID')):
			raise tornado.web.HTTPError(400, '参数 Error')

		videoInstance = self.service.video_dwz(data)
		if videoInstance == None:
			raise tornado.web.HTTPError(404, '视频不存在')

		self.__reponseJSON(videoInstance)

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
		if not self.__has_params(data, ('UserKey', 'VID')):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON(self.service.video_remove(data))



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
			Results[Array] – 分享结果对象列表，分享结果对象如下定义：
				Mobile[string] – 分享手机号
				Signup[boolean] – 是否注册用户
		"""
		if not self.__has_params(data, ('UserKey', 'VID', 'To')):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON(self.service.share_video(data))


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
				to_names[date] – 分享日期
				VID[string] – 视频ID
		"""

		if not self.__has_params(data, ['UserKey']):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON(self.service.share_list(data))


	def short_url(self, data):
		"""
		获取短地址
		方法：
			short_url
		参数：
			URL[string] – 需要转换的URL
		返回值：
			URL[string] – 转换的URL
			SHORT_URL[string] – 短URL
		"""
		if not self.__has_params(data, ('URL')):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON({
			'URL'		: data.get('URL'),
			'SHORT_URL'	: getShortUrl(data.get('URL'))
		})


	def short_url_get(self, data):
		"""
		通过短地址获取原URL
		方法：
			short_url_get
		参数：
			URL[string] – 短URL
		返回值：
			URL[string] – 原URL
			SHORT_URL[string] – 短URL
		"""
		if not self.__has_params(data, ('URL')):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON({
			'URL'		: getUrl(str(data.get('URL'))),
			'SHORT_URL'	: data.get('URL')
		})


	def publishvideo(self, data):
		multiprocessing.Process(target=Download, args=(data,)).start()
		pass





def sig_handler(sig, frame):
	logging.warning('Caught signal: %s', sig)
	tornado.ioloop.IOLoop.instance().add_callback(shutdown)

MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 3

def shutdown():
	logging.info('Stopping http server')
	http_server.stop()

	logging.info('Will shutdown in %s seconds ...', MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
	io_loop = tornado.ioloop.IOLoop.instance()

	deadline = time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN

	def stop_loop():
		now = time.time()
		if now < deadline and (io_loop._callbacks or io_loop._timeouts):
			io_loop.add_timeout(now + 1, stop_loop)
		else:
			io_loop.stop()
			logging.info('Shutdown')

	stop_loop()


def startup(applicationConfig):

	host = applicationConfig.get('Server','IP')
	port = applicationConfig.getint('Server','Listen')
	
	signal.signal(signal.SIGTERM, sig_handler)
	signal.signal(signal.SIGINT, sig_handler)

	pid = os.getpid()

	f = open('server.pid', 'wb')
	f.write(str(pid))
	f.close()

	service = Service(applicationConfig)
	
	application = tornado.web.Application([
		(r"/s/(.*)", ShortUrlHandler),
		(r"/api/(.*)", MainHandler, dict(service=service)),
		(r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "./static"}),
	])

	global http_server
	print "Startup server on %s:%d, PID:%d ..." % (host,port,pid)
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.bind(port, host)
	http_server.start(num_processes = applicationConfig.getint('Server','NumProcesses')) # tornado将按照cpu核数来fork进程
	tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
	applicationConfig = ConfigParser()
	applicationConfig.read('Config.ini')
	startup(applicationConfig)
