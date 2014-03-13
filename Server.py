# -*- encoding: utf-8 -*-


from datetime import date
from urlparse import urljoin
from urlparse import urlsplit
from datetime import datetime
from datetime import timedelta
from ConfigParser import ConfigParser

from Service import Service

import os
import uuid
import json
import time
import signal
import logging
import hashlib
import httplib
import tornado.web
import tornado.ioloop
import tornado.httpserver
import dateutil
import dateutil.tz
import dateutil.parser


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
			'validate'			: self.validate,
			'login'				: self.login,
			'settings'			: self.settings,
			'videoid'			: self.videoid,
			'upload_progress'	: self.upload_progress,
			'upload'			: self.upload,
			'setvideo'			: self.setvideo,
			'getvideo'			: self.getvideo,
			'share'				: self.share,
			'list'				: self.list,
		}

	def post(self, api):
		if 'application/json' == self.request.headers['Content-Type']:
			self.urlmap.get(api, self.__responseDefault)(json.loads(self.request.body))
		else:
			raise tornado.web.HTTPError(400, '数据格式不支持')
	
	def __responseDefault(self,data):
		raise tornado.web.HTTPError(400, '功能不支持')

	def __reponseJSON(self, data):
		self.set_header('Content-Type', 'application/json')
		self.set_header('Server', 'Video API Server')
		self.write(json.dumps(data, cls=MyJSONEncoder))

	def __has_params(self, data, params):
		if not isinstance(data, dict):
			return False
		for p in params:
			if not data.has_key(p):
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
		if not self.__has_params(data, ('Mobile', 'Device')):
			raise tornado.web.HTTPError(400, '参数Error')

		self.__reponseJSON({
			'Now': datetime.now(),
			'ValidityDate': datetime.now() + timedelta(seconds=90)
			})
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
			UserKey[string] – 用户登录后的会话ID。（用于后续功能调用）
			NewUser[boolean] - 新用户
		"""
		if not self.__has_params(data, ('Mobile', 'Validate')):
			raise tornado.web.HTTPError(400, '参数Error')

		self.__reponseJSON({
			'Error': 0,
			'Now': datetime.now()
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



	def videoid(self, data):
		"""
		分配视频ID
		方法：
			videoid
		参数：
			UserKey[string] –用户登录后的会话ID。
			Length[long] –视频字节数，单位BYTES。
		返回值：
			VID[string] – 分配的视频ID
			Length[long] – 视频字节数，单位BYTES。
		"""
		if not self.__has_params(data, ('UserKey', 'Length')):
			raise tornado.web.HTTPError(400, '参数 Error')

		vid = self.service.uploadid(data)
		self.__reponseJSON({
			'Now': datetime.now(),
			'VID': vid,
			'Length': data['Length']
			})
		pass


	def upload_progress(self, data):
		"""
		获取视频上传进度
		方法：
			upload_progress
		参数：
			UserKey[string] –用户登录后的会话ID。
			VID[string] – 分配的视频ID
		返回值：
			Error[long] – 发送成功返回0，否则返回非零值。
			VID[string] – 分配的视频ID
			Saved[long] – 上传字节数，单位BYTES。
			Length[long] – 视频字节数，单位BYTES。
		"""
		if not self.__has_params(data, ('UserKey', 'VID')):
			raise tornado.web.HTTPError(400, '参数 Error')

		length, saved = self.service.upload_progress(data)
		self.__reponseJSON({
			'Now'   : datetime.now(),
			'VID'   : data['VID'],
			'Length': length,
			'Saved' : saved,
			})
		pass

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
			Error[long] – 发送成功返回0，否则返回非零值。
			Saved[long] – 上传字节数，单位BYTES。
			Length[long] – 视频字节数，单位BYTES。
		"""
		if not self.__has_params(data, ('UserKey', 'VID', 'Offset', 'Data', 'Size')):
			raise tornado.web.HTTPError(400, '参数 Error')

		length, saved = self.service.upload(data)

		self.__reponseJSON({
			'Now'   : datetime.now(),
			'VID'   : data['VID'],
			'Length': length,
			'Saved' : saved,
			})
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
		if not self.__has_params(data, ('UserKey', 'VID')):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON({
			'Now': datetime.now()
			})
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
		if not self.__has_params(data, ('UserKey', 'VID')):
			raise tornado.web.HTTPError(400, '参数 Error')

		videoInstance = self.service.getvideo(data)
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
		if not self.__has_params(data, ('UserKey', 'VID', 'To')):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON({
			'Now': datetime.now()
			})
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
		if not self.__has_params(data, ('UserKey', 'Offset', 'Max')):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON({
			'Now': datetime.now()
			})
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
		(r"/api/(.*)", MainHandler, dict(service=service)),
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
