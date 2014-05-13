#coding=utf-8
#-*- encoding: utf-8 -*-

from datetime import date,datetime,timedelta
from Downloader import Download

import multiprocessing
import httplib,json,re
import tornado.web, tornado.ioloop, tornado.httpserver, tornado.template

import StringIO
import Config, Utils
import UserService, UploadService, VideoService, ShareService, ShortUrlService, SpaceService

class APIHandler(tornado.web.RequestHandler):


	def initialize(self):
		self.urlmap = {
			'validate'          : 'user_validate',
			'userkey'           : 'user_id',
			'login'             : 'user_auth',
			'uploadid'          : 'upload_id',
			'upload'            : 'upload_data',
			'createvideo'       : 'video_create',
			'getvideo'          : 'video_get',
			'sharevideo'        : 'share_video',
			'listsharevideo'    : 'share_list',
		}


	def post(self, api):
		if 'application/json' in self.request.headers['Content-Type']:
			try:
				func = getattr(self, self.urlmap.get(api, api))
				func(json.loads(self.request.body))
			except AttributeError as e:
				raise tornado.web.HTTPError(400, '功能不支持')
		else:
			raise tornado.web.HTTPError(400, '数据格式不支持')


	def get(self, api):
		if api != 'doc':
			raise tornado.web.HTTPError(404)

		self.set_header('Content-Type', 'text/html; charset=UTF-8')

		data = []
		funlist = APIHandler.__dict__
		for m in sorted(funlist.iterkeys()):
			doc = funlist[m].__doc__
			if m[0] != '_' and doc:
				lines = []
				for line in doc.splitlines():
					line = re.sub(r'^\t\t', '', line).strip()
					if len(line) > 0:
						lines.append(line)
				data.append({
					'name': m,
					'lines': lines
					})

		loader = tornado.template.Loader("./tpl")
		self.write(loader.load("doc.html").generate(data=data))


	def __reponseJSON(self, data):
		self.set_header('Content-Type', 'application/json')
		self.set_header('Server', 'VideoServer')
		self.write(Utils.json_dumps(data))

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
	#   self.set_header('Content-Type', 'application/json')
	#   self.set_header('Server', 'Video API Server')
	#   self.write({'Error': -1, 'Message': str(e)})

	###########################################################################
	#
	# API 功能实现 - 用户类
	#
	###########################################################################
	
	def user_id(self, data):
		"""
		获取用户信息
		参数：
			UserKey[string] – 用户登录后的会话ID
		返回值：
			UserId[String] – 用户ID
			Name[String] – 用户姓名
			Login[String] – 用户绑定的登录账户
			Mobile[String] – 用户绑定的手机号
			Email[String] – 用户绑定的邮箱
		"""
		if not self.__has_params(data, ('UserKey')):
			raise tornado.web.HTTPError(400, '参数Error')

		userId = UserService.user_id(data['UserKey'])
		user = UserService.user_get(userId)

		self.__reponseJSON({
			'UserId'    : userId,
			'Name'      : user['name'],
			'Mobile'    : user['mobile'],
			'Login'     : user['login'],
			'Email'     : user['email'],
		})


	def user_password(self, data):
		"""
		更改用户登录密码
		参数：
			UserKey[string] – 用户登录后的会话ID
			Password[string] – 用户设置的密码，建议在客户端通过MD5加密传输
		返回值：
			UserId[String] – 用户ID
		"""
		if not self.__has_params(data, ('UserKey', 'Password')):
			raise tornado.web.HTTPError(400, '参数Error')

		userId = UserService.user_password(data)
		self.__reponseJSON({
			'UserId' : userId,
		})
	

	def user_validate(self, data):
		"""
		发送短信验证码
		参数：
			Mobile[string] – 用户手机号码
			Device[string] – 设备名称
		返回值：
			ValidityDate[date] – 验证码有效日期。
		"""
		if not self.__has_params(data, ('Mobile', 'Device')):
			raise tornado.web.HTTPError(400, '参数Error')

		validityDate = UserService.user_validate(data)

		self.__reponseJSON({ 
			'ValidityDate'  : validityDate,
		})


	def user_auth(self, data):
		"""
		验证用户身份
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

		result = UserService.user_auth(data)
		if not result or not result['UserKey']:
			raise tornado.web.HTTPError(500, '验证码或用户名、密码错误!') 

		self.__reponseJSON({
			'Now'     : datetime.now(),
			'UserKey' : result['UserKey'],
			'NewUser' : result['NewUser'],
			'ValidityDate' : result['ValidityDate']
			})
		pass



	def settings(self, data):
		"""
		更新用户设置
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


	###########################################################################
	#
	# API 功能实现 - 数据上传类
	#
	###########################################################################
	

	def upload_id(self, data):
		"""
		分配上传会话ID
		参数：
			UserKey[string] –用户登录后的会话ID。
			Length[long] – 文件字节数，单位BYTES。
		返回值：
			UploadId[string] – 分配的上传会话ID
			Length[long] – 文件字节数，单位BYTES。
		"""
		if not self.__has_params(data, ('UserKey', 'Length')):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON({
			'Now'       : datetime.now(),
			'UploadId'  : UploadService.upload_id(data),
			'Length'    : data['Length']
			})
		pass


	def upload_progress(self, data):
		"""
		获取上传进度
		参数：
			UserKey[string] –用户登录后的会话ID。
			UploadId[string] – 分配的上传会话ID
		返回值：
			Error[long] – 发送成功返回0，否则返回非零值。
			UploadId[string] – 分配的上传会话ID
			Saved[long] – 上传字节数，单位BYTES。
			Length[long] – 文件字节数，单位BYTES。
		"""
		if not self.__has_params(data, ('UserKey', 'UploadId')):
			raise tornado.web.HTTPError(400, '参数 Error')

		progress = UploadService.upload_progress(data)
		self.__reponseJSON({
			'Now'       : datetime.now(),
			'UploadId'  : data['UploadId'],
			'Length'    : progress['length'],
			'Saved'     : progress['saved'],
			})
		pass

	def upload_data(self, data):
		"""
		上传数据
		参数：
			UserKey[string] –用户登录后的会话ID。
			UploadId[string] – 分配的上传会话ID
			Offset[long] – 文件偏移，单位BYTES。
			Data[string] – 数据包，经Base64编码后的数据包。
			Size[long] – 数据包包含数据大小（Base64编码前）。
		返回值：
			Saved[long] – 上传字节数，单位BYTES。
			Length[long] – 视频字节数，单位BYTES。
		"""
		if not self.__has_params(data, ('UserKey', 'UploadId', 'Offset', 'Data', 'Size')):
			raise tornado.web.HTTPError(400, '参数 Error')

		progress = UploadService.upload_data(data)

		self.__reponseJSON({
			'UploadId'  : data['UploadId'],
			'Length'    : progress['length'],
			'Saved'     : progress['saved'],
			})
		pass


	###########################################################################
	#
	# API 功能实现 - 视频类
	#
	###########################################################################
	
	def video_create(self, data):
		"""
		创建视频信息
		参数：
			UserKey[string] –用户登录后的会话ID。
			UploadId[string] – 分配的上传会话ID
			Title[string] – 视频标题
			Author[string] – 分享者/创作者名称
			CreateTime[date] – 创作日期
			Category[string] – 视频分类
			Describe[string] – 视频描述
			Tag[string] – 视频标签，标签内容有半角“,”（逗号）分割
			AddrStr[string] - 视频位置信息
			Longitude[float] - 视频位置 - 经度
			Latitude[float] - 视频位置 - 纬度
		返回值：
			VID[string] – 视频ID
		"""
		if not self.__has_params(data, ('UserKey', 'UploadId')):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON({
			'VID': VideoService.video_create(data)
			})
		pass


	def video_ready(self, data):
		"""
		视频处理状态
		参数：
			UserKey[string] –用户登录后的会话ID。
			VID[string] – 视频ID
		返回值：
			VID[string] – 视频ID
			Results[Array] – 视频对象列表，视频对象定义如下：
				Definition[string] - 清晰度
				Ready[boolean] - 是否准备就绪
				URL[string] – 视频所有者，默认为视频上传/分享者的手机号
				Progress[float] – 处理进度
		"""
		if not self.__has_params(data, ('UserKey', 'VID')):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON({
			'Now': datetime.now(),
			'VID': data['VID'],
			'Results': VideoService.video_ready(data)
			})



	def video_update(self, data):
		"""
		更新视频信息
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
			'VID': VideoService.video_update(data)
			})
		pass


	def video_list(self, data):
		"""
		获取视频列表
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
				AddrStr[string] - 视频位置信息
				Longitude[float] - 视频位置 - 经度
				Latitude[float] - 视频位置 - 纬度
				Duration[long] – 视频长度
				Definition[long] – 视频清晰度： 0:流畅，1:标清，2:高清，3:超清
				PosterURLs[array] – 视频截图URLs，JPG文件
				VideoURLs[array] – 视频播放URLs，数量参考清晰度(清晰度+1)
		"""
		if not self.__has_params(data, ['UserKey']):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON(VideoService.video_list(data))


	def video_get(self, data):
		"""
		获取视频信息
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
			AddrStr[string] - 视频位置信息
			Longitude[float] - 视频位置 - 经度
			Latitude[float] - 视频位置 - 纬度
			Duration[long] – 视频长度
			Definition[long] – 视频清晰度： 0:流畅，1:标清，2:高清，3:超清
			PosterURLs[array] – 视频截图URLs，JPG文件，1~5个。
			VideoURLs[array] – 视频播放URLs，数量参考清晰度(清晰度+1)
		"""
		if not self.__has_params(data, ('UserKey', 'VID')):
			raise tornado.web.HTTPError(400, '参数 Error')

		videoInstance = VideoService.video_get(data)
		if videoInstance == None:
			raise tornado.web.HTTPError(404, '视频不存在')

		self.__reponseJSON(videoInstance)


	def video_poster(self, data):
		"""
		更新视频截图
		方法：
			video_poster
		参数：
			UserKey[string] –用户登录后的会话ID。
			VID[string] – 分配的视频ID
			Time[float] – 截图播放时间点
		返回值：
			VID[string] – 视频ID
			Poster[string] – 视频截图地址
		"""
		if not self.__has_params(data, ('UserKey', 'VID')):
			raise tornado.web.HTTPError(400, '参数 Error')

		videoInstance = VideoService.video_poster(data)
		if videoInstance == None:
			raise tornado.web.HTTPError(404, '视频不存在')

		self.__reponseJSON(videoInstance)


	def video_dwz(self, data):
		"""
		获取视频播放短地址
		参数：
			UserKey[string] –用户登录后的会话ID。
			VID[string] – 分配的视频ID
		返回值：
			VID[string] – 视频ID
			URL[string] – 视频短地址
		"""
		if not self.__has_params(data, ('UserKey', 'VID')):
			raise tornado.web.HTTPError(400, '参数 Error')

		videoInstance = VideoService.video_dwz(data)
		if videoInstance == None:
			raise tornado.web.HTTPError(404, '视频不存在')

		self.__reponseJSON(videoInstance)


	def video_remove(self, data):
		"""
		删除视频
		参数：
			UserKey[string] –用户登录后的会话ID。
			VID[string] – 分配的视频ID
		返回值：
			VID[string] – 删除的视频ID
		"""
		if not self.__has_params(data, ('UserKey', 'VID')):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON(VideoService.video_remove(data))



	###########################################################################
	#
	# API 功能实现 - 分享类
	#
	###########################################################################
	
	def share_video(self, data):
		"""
		分享视频
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

		self.__reponseJSON(ShareService.share_video(data))


	def share_list(self, data):
		"""
		获取分享列表
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

		self.__reponseJSON(ShareService.share_list(data))


	###########################################################################
	#
	# API 功能实现 - 短地址服务
	#
	###########################################################################
	
	def short_url(self, data):
		"""
		获取短地址
		参数：
			URL[string] – 需要转换的URL
		返回值：
			URL[string] – 原URL
			SHORT_URL[string] – 短URL
		"""
		if not self.__has_params(data, ('URL')):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON({
			'URL'       : data.get('URL'),
			'SHORT_URL' : ShortUrlService.createShortUrl(data.get('URL'))
		})


	def short_url_reverse(self, data):
		"""
		通过短地址获取原URL
		参数：
			URL[string] – 短URL
		返回值：
			URL[string] – 原URL
			SHORT_URL[string] – 短URL
		"""
		if not self.__has_params(data, ('URL')):
			raise tornado.web.HTTPError(400, '参数 Error')

		self.__reponseJSON({
			'URL'       : ShortUrlService.reverseShortUrl(str(data.get('URL'))),
			'SHORT_URL' : data.get('URL')
		})


	###########################################################################
	#
	# API 功能实现 - 代理下载功能服务
	#
	###########################################################################
	
	def publishvideo(self, data):
		multiprocessing.Process(target=Download, args=(data,)).start()
		pass


	###########################################################################
	#
	# API 功能实现 - 空间服务
	#
	###########################################################################
	
	def space_list(self, data):
		"""
		用户个人空间列表（全部）
		参数：
			UserKey[string] – 用户会话ID
		返回值：
			Count[long] – 列表数量（全部）
			Spaces[Array] – 空间对象列表：
				Id[string] – 空间唯一编号
				Name[string] – 空间名称
		"""
		self.__reponseJSON({
			'Now': datetime.now(),
			})
		

	def space_create(self, data):
		"""
		创建用户个人空间
		参数：
			UserKey[string] – 用户会话ID
			Name[string] – 空间名称
			After[string] – 排在...空间之后[可选]：空间ID编号；如果为'HEAD'，则创建在最开始；如果不提供，则默认最后位置
		返回值：
			Id[string] – 空间唯一编号
			Name[string] – 空间名称
		"""
		self.__reponseJSON({
			'Now': datetime.now(),
			})

	def space_rename(self, data):
		"""
		更改用户个人空间名称
		参数：
			UserKey[string] – 用户会话ID
			Id[string] – 空间唯一编号
			Name[string] – 新的空间名称
		返回值：
			Id[string] – 空间唯一编号
			Name[string] – 空间名称
		"""
		self.__reponseJSON({
			'Now': datetime.now(),
			})

	def space_reindex(self, data):
		"""
		更改用户个人空间排序位置
		参数：
			UserKey[string] – 用户会话ID
			Id[string] – 空间唯一编号
			After[string] – 排在...空间之后：空间ID编号；如果为'HEAD'，则创建在最开始；如果不提供，则默认最后位置
		返回值：
			Id[string] – 空间唯一编号
			Name[string] – 空间名称
		"""
		self.__reponseJSON({
			'Now': datetime.now(),
			})

	def space_res_relation(self, data):
		"""
		用户个人空间增加资源
		参数：
			UserKey[string] – 用户会话ID
			Id[string] – 空间唯一编号
			ResType[string] - 资源类型
			ResId[string] - 资源唯一编号
			OrderField1[int] – 排序字段1[可选]
			OrderField2[int] – 排序字段2[可选]
			OrderField3[int] – 排序字段3[可选]
		返回值：
			Id[string] – 空间唯一编号
			ResType[string] - 资源类型
			ResId[string] - 资源唯一编号
		"""
		self.__reponseJSON({
			'Now': datetime.now(),
			})

	def space_res_unrelation(self, data):
		"""
		用户个人空间资源移除
		参数：
			UserKey[string] – 用户会话ID
			Id[string] – 空间唯一编号
			ResType[string] - 资源类型
			ResId[string] - 资源唯一编号
		返回值：
			Id[string] – 空间唯一编号
			ResType[string] - 资源类型
			ResId[string] - 资源唯一编号
		"""
		self.__reponseJSON({
			'Now': datetime.now(),
			})

	def space_res_order(self, data):
		"""
		用户个人空间资源排序字段更新
		参数：
			UserKey[string] – 用户会话ID
			Id[string] – 空间唯一编号
			ResType[string] - 资源类型
			ResId[string] - 资源唯一编号
			OrderField1[int] – 排序字段1[可选]
			OrderField2[int] – 排序字段2[可选]
			OrderField3[int] – 排序字段3[可选]
		返回值：
			Id[string] – 空间唯一编号
			ResType[string] - 资源类型
			ResId[string] - 资源唯一编号
		"""
		self.__reponseJSON({
			'Now': datetime.now(),
			})

	def space_res_list(self, data):
		"""
		用户个人空间资源列表
		参数：
			UserKey[string] – 用户会话ID
			Id[string] – 空间唯一编号
			ResType[string] - 资源类型
			Offset[long] – 起始位置[可选]，默认0
			Max[long] – 最大返回条数[可选]，默认10
			Sort[int] - 排序字段编号[可选]，可选值：1~3
			Order[int] - 排序方法[可选]，可选值：0-增序/1-降序
		返回值：
			Id[string] – 空间唯一编号
			ResType[string] - 资源类型
			Count[long] – 列表数量（全部）
			Offset[long] – 列表起始位置。
			Max[long] – 列表最大条数
			Sort[int] - 排序字段编号[可选]，可选值：1~3
			Order[int] - 排序方法[可选]，可选值：0-增序/1-降序
			Results[Array] – 空间对象列表：
				ResId[string] - 资源唯一编号
		"""
		self.__reponseJSON({
			'Now': datetime.now(),
			})

	def space_authorize(self, data):
		"""
		用户个人空间授权
		参数：
			UserKey[string] – 用户会话ID
			Id[string] – 空间唯一编号
			UserId[string] – 授权用户ID
			AllowEdit[int] – 是否允许修改[可选]，0-只读(默认)/1-可修改
		返回值：
			Id[string] – 空间唯一编号
			Name[string] – 空间名称
			UserId[string] – 授权用户ID
			UserName[string] – 授权用户名
			AllowEdit[int] – 是否允许修改[可选]，0-只读(默认)/1-可修改
		"""
		self.__reponseJSON({
			'Now': datetime.now(),
			})

	def space_authorize_list(self, data):
		"""
		用户个人空间授权用户列表
		参数：
			UserKey[string] – 用户会话ID
			Id[string] – 空间唯一编号
		返回值：
			Id[string] – 空间唯一编号
			Name[string] – 空间名称
			Results[Array] – 授权对象列表：
				UserId[string] – 授权用户ID
				UserName[string] – 授权用户名
				AllowEdit[int] – 是否允许修改，0-只读/1-可修改
		"""
		self.__reponseJSON({
			'Now': datetime.now(),
			})

