# -*- encoding: utf-8 -*-


from datetime import date
from urlparse import urljoin
from urlparse import urlsplit
from datetime import datetime
from datetime import timedelta
from Service import Service


import os
import uuid
import json
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

	def write_error(self, status_code, **kwargs):
		self.__reponseJSON({'Error': status_code, 'Message': httplib.responses[status_code]})


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
			Error[long] – 发送成功返回0，否则返回非零值。
			Message[string] – 返回消息，如果非零，则返回错误信息。
			ValidityDate[date] – 验证码有效日期。
		"""
		self.__reponseJSON({
			'Error': 0,
			'Message': '',
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
			Error[long] – 发送成功返回0，否则返回非零值。
			Message[string] – 返回消息，如果非零，则返回错误信息。
			UserKey[string] – 用户登录后的会话ID。（用于后续功能调用）
			NewUser[boolean] - 新用户
		"""
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
			Error[long] – 发送成功返回0，否则返回非零值。
			Key[string] – 参数名
			Value[string] – 参数当前设置的值
		"""
		self.__reponseJSON({
			'Error': 0,
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
			Error[long] – 发送成功返回0，否则返回非零值。
			VID[string] – 分配的视频ID
			Length[long] – 视频字节数，单位BYTES。
		"""
		self.__reponseJSON({
			'Error': 0,
			'Now': datetime.now(),
			'VID': self.service.generateVideoId(data),
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
		self.__reponseJSON({
			'Error' : 0,
			'Now'   : datetime.now(),
			'VID'   : data['VID'],
			'Length': 0,
			'Saved' : 0,
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
		self.__reponseJSON({
			'Error' : 0,
			'Now'   : datetime.now(),
			'VID'   : data['VID'],
			'Length': 0,
			'Saved' : 0,
			})
		pass


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
		self.__reponseJSON({
			'Error': 0,
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
		self.__reponseJSON({
			'Error': 0,
			'Now': datetime.now()
			})
		pass

	

def startup(port, host='0.0.0.0'):
	
	service = Service()
	
	application = tornado.web.Application([
		(r"/api/(.*)", MainHandler, dict(service=service)),
	])
										   
	print "Startup server on %s:%d ..." % (host,port)
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.bind(port, host)
	http_server.start(num_processes=0) # tornado将按照cpu核数来fork进程
	tornado.ioloop.IOLoop.instance().start()	


if __name__ == "__main__":
	startup(9000)
