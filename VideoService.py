#coding=utf-8
#-*- encoding: utf-8 -*-

from datetime import datetime, timedelta
from MySQL import MySQL
from MediaProbe import MediaProbe
from Transcoder import Transcoder, TranscodeTemplates

import os
import Config
import Utils
import UserService, ShortUrlService


uploadDirectory = Config.get('Server','Upload')
videoDirectory = Config.get('Video','SavePath')

# auto create directory
if not os.path.exists(videoDirectory):
	os.makedirs(videoDirectory)


def video_create(data):
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
		AddrStr[string] - 视频位置信息
		Longitude[float] - 视频位置 - 经度
		Latitude[float] - 视频位置 - 纬度
	返回值：
		VID[string] – 视频ID
	"""

	userId = UserService.user_id(data['UserKey'])

	fileName = "%s/%s" % (uploadDirectory, data['UploadId'])

	db = MySQL()
	newId = Utils.UUID()
	media = MediaProbe(fileName)

	# media.createTime()
	result = db.save("""INSERT INTO `video` (`id`, `upload_id`, `owner_id`, `duration`, `video_width`, `video_height`, `video_bitrate`, `title`, `author`, `create_date`, `category`, `describe`, `tag`, `lbs_addr`, `lbs_lon`, `lbs_lat`) 
						VALUES (%s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s,%s)""",
					(newId, data['UploadId'], userId, media.duration(), media.videoWidth(), media.videoHeight(), media.videoBitrate(), 
					data.get('Title', ''),
					data.get('Author', ''),
					data.get('CreateTime', media.createTime()),
					data.get('Category', ''),
					data.get('Describe', ''),
					data.get('Tag', ''),
					data.get('AddrStr', None),
					data.get('Longitude', None),
					data.get('Latitude', None)))
	db.end()

	# 截图
	destFileName = "%s/%s.jpg" % (videoDirectory, newId)
	Transcoder.VideoPoster(fileName, destFileName)

	# post transcode task
	# 原清晰度
	if media.videoCodec() == 'h264' and media.audioCodec() == 'aac' :
		result = db.save("""INSERT INTO `video_transcode` (`video_id`, `file_name`, `video_width`, `video_height`, `video_bitrate`, `video_codec`, `audio_channels`, `audio_bitrate`, `audio_codec`) 
							VALUES (%s,%s,%s,%s,%s, %s,%s,%s,%s)""",
						(newId, newId + '.mp4',
							media.videoWidth(),
							media.videoHeight(),
							media.videoBitrate(),
							'copy',
							media.audioChannels(),
							media.audioBitrate(),
							'copy'))
		taskId = db.getInsertId()
		db.end()
	else:
		result = db.save("""INSERT INTO `video_transcode` (`video_id`, `file_name`, `video_width`, `video_height`, `video_bitrate`, `video_codec`, `audio_channels`, `audio_bitrate`, `audio_codec`) 
							VALUES (%s,%s,%s,%s,%s, %s,%s,%s,%s)""",
						(newId, newId + '.mp4',
							media.videoWidth(),
							media.videoHeight(),
							media.videoBitrate(),
							TranscodeTemplates.HD['video_codec'],
							media.audioChannels(),
							media.audioBitrate(),
							TranscodeTemplates.HD['audio_codec'] ))
		taskId = db.getInsertId()
		db.end()

	# 高清
	if media.supportHD() and not media.DefinitionIsHD():
		result = db.save("""INSERT INTO `video_transcode` (`video_id`, `file_name`, `video_width`, `video_height`, `video_bitrate`, `video_codec`, `audio_channels`, `audio_bitrate`, `audio_codec`) 
							VALUES (%s,%s,%s,%s,%s, %s,%s,%s,%s)""",
						(newId, newId + '_hd.mp4', 
							int(TranscodeTemplates.HD['video_width']), 
							int(TranscodeTemplates.HD['video_width']) / media.videoAspect(),
							TranscodeTemplates.HD['video_bitrate'], 
							TranscodeTemplates.HD['video_codec'],
							TranscodeTemplates.HD['audio_channel'],
							TranscodeTemplates.HD['audio_bitrate'],
							TranscodeTemplates.HD['audio_codec'] ))
		taskId = db.getInsertId()
		db.end()

	# 标清
	if media.supportSD() and not media.DefinitionIsSD():
		result = db.save("""INSERT INTO `video_transcode` (`video_id`, `file_name`, `video_width`, `video_height`, `video_bitrate`, `video_codec`, `audio_channels`, `audio_bitrate`, `audio_codec`) 
							VALUES (%s,%s,%s,%s,%s, %s,%s,%s,%s)""",
						(newId, newId + '_sd.mp4', 
							int(TranscodeTemplates.SD['video_width']), 
							int(TranscodeTemplates.SD['video_width']) / media.videoAspect(),
							TranscodeTemplates.SD['video_bitrate'], 
							TranscodeTemplates.SD['video_codec'],
							TranscodeTemplates.SD['audio_channel'],
							TranscodeTemplates.SD['audio_bitrate'],
							TranscodeTemplates.SD['audio_codec'] ))
		taskId = db.getInsertId()
		db.end()

	# 流畅
	if media.supportSD():
		result = db.save("""INSERT INTO `video_transcode` (`video_id`, `file_name`, `video_width`, `video_height`, `video_bitrate`, `video_codec`, `audio_channels`, `audio_bitrate`, `audio_codec`) 
							VALUES (%s,%s,%s,%s,%s, %s,%s,%s,%s)""",
						(newId, newId + '_small.mp4', 
							int(TranscodeTemplates.CIF['video_width']), 
							int(TranscodeTemplates.CIF['video_width']) / media.videoAspect(),
							TranscodeTemplates.CIF['video_bitrate'], 
							TranscodeTemplates.CIF['video_codec'],
							TranscodeTemplates.CIF['audio_channel'],
							TranscodeTemplates.CIF['audio_bitrate'],
							TranscodeTemplates.CIF['audio_codec'] ))
		taskId = db.getInsertId()
		db.end()

	return newId


def video_update(data):
	"""
	更新视频信息
	参数：
		UserKey[string] –用户登录后的会话ID。
		VID[string] – 视频ID
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

	userId = UserService.user_id(data['UserKey'])
	videoId = data.get('VID', '')

	db = MySQL()
	db.update("UPDATE `video` set `title` = %s, `author` = %s, `create_date` = %s, `category` = %s, `describe` = %s, `tag` = %s  WHERE `id` = %s AND `owner_id` = %s ", (
		data.get('Title', ''),
		data.get('Author', ''),
		data.get('CreateTime', ''),
		data.get('Category', ''),
		data.get('Describe', ''),
		data.get('Tag', ''),
		videoId,
		userId))

	db.end()
		
	return data.get('VID', '')




def video_list(data):
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
			AddrStr[string] - 视频位置信息
			Longitude[float] - 视频位置 - 经度
			Latitude[float] - 视频位置 - 纬度
			Duration[long] – 视频长度
			Published[string] - 发布时间
			Definition[long] – 视频清晰度： 0:流畅，1:标清，2:高清，3:超清
			PosterURLs[array] – 视频截图URLs，JPG文件
			VideoURLs[array] – 视频播放URLs，数量参考清晰度(清晰度+1)
	"""
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()

	offset = data.get('Offset', 0)
	sort = data.get('Sort', 'create_time')
	order = data.get('Order', 'DESC')
	listMax = min(100, data.get('Max', 10))
	count = long(db.get('SELECT count(id) as c FROM `video` WHERE `owner_id` = %s', userId).get('c'))

	results = []

	videoListInstance = db.list('SELECT * FROM `video` WHERE `owner_id` = %s ORDER BY `create_time` DESC LIMIT %s,%s', (userId, offset, listMax))

	PosterBaseURL = Config.get('Video','PosterBaseURL')
	VideoBaseURL = Config.get('Video','VideoBaseURL')

	for videoInstance in videoListInstance:

		VideoURLs = []
		video_urls = []
		VideoBaseURL = Config.get('Video','VideoBaseURL')

		VideoURLs.append("%s/%s.mp4" % (VideoBaseURL,videoInstance['id']))

		videoTranscodeListInstance = db.list('SELECT * FROM `video_transcode` WHERE `video_id` = %s ORDER BY `video_width` DESC', (videoInstance['id']))
		for videoTranscodeInstance in videoTranscodeListInstance:
			if videoTranscodeInstance['is_ready']:
				VideoURLs.append("%s/%s" % (VideoBaseURL, videoTranscodeInstance['file_name']))
			video_urls.append({
				'Definition': MediaProbe.definitionName(videoTranscodeInstance['video_height'], videoTranscodeInstance['video_width']),
				'Ready'     : videoTranscodeInstance['is_ready'] == 1,
				'URL'       : "%s/%s" % (VideoBaseURL, videoTranscodeInstance['file_name']),
				'Progress'  : float(videoTranscodeInstance['progress']),
			})

		results.append({
			'VID'       : videoInstance['id'],
			'Owner'     : UserService.user_mobile(videoInstance['owner_id']),
			'Title'     : videoInstance['title'],
			'Author'    : videoInstance['author'],
			'CreateTime': videoInstance['create_date'],
			'Category'  : videoInstance['category'],
			'Describe'  : videoInstance['describe'],
			'Tag'       : videoInstance['tag'],
			'AddrStr'	: videoInstance['lbs_addr'],
			'Longitude'	: videoInstance['lbs_lon'],
			'Latitude'	: videoInstance['lbs_lat'],
			'Duration'  : videoInstance['duration'],
			'Published' : videoInstance['create_time'],
			'Definition': MediaProbe.definition(videoInstance['video_height']),
			'Poster'    : "%s/%s.jpg" % (PosterBaseURL, videoInstance['id']),
			'PosterURLs': ("%s/%s.jpg" % (PosterBaseURL, videoInstance['id']), ),
			'VideoURLs' : VideoURLs,
			'Videos'    : video_urls,
		})

	return {
		'Count'     : count,
		'Offset'    : offset,
		'Max'       : listMax,
		'Results'   : results,
	}



def video_get(data):
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
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()
	videoInstance = db.get('SELECT * FROM `video` WHERE `id` = %s', (data['VID']))
	if videoInstance:
		PosterBaseURL = Config.get('Video','PosterBaseURL')
		VideoBaseURL = Config.get('Video','VideoBaseURL')

		VideoURLs = []
		video_urls = []
		VideoBaseURL = Config.get('Video','VideoBaseURL')

		VideoURLs.append("%s/%s.mp4" % (VideoBaseURL,videoInstance['id']))

		videoTranscodeListInstance = db.list('SELECT * FROM `video_transcode` WHERE `video_id` = %s ORDER BY `video_width` DESC', (videoInstance['id']))
		for videoTranscodeInstance in videoTranscodeListInstance:
			if videoTranscodeInstance['is_ready']:
				VideoURLs.append("%s/%s" % (VideoBaseURL, videoTranscodeInstance['file_name']))
			video_urls.append({
				'Definition': MediaProbe.definitionName(videoTranscodeInstance['video_height'], videoTranscodeInstance['video_width']),
				'Ready'     : videoTranscodeInstance['is_ready'] == 1,
				'URL'       : "%s/%s" % (VideoBaseURL, videoTranscodeInstance['file_name']),
				'Progress'  : float(videoTranscodeInstance['progress']),
			})

		return {
			'VID'       : videoInstance['id'],
			'Owner'     : UserService.user_mobile(videoInstance['owner_id']),
			'Title'     : videoInstance['title'],
			'Author'    : videoInstance['author'],
			'CreateTime': videoInstance['create_date'],
			'Category'  : videoInstance['category'],
			'Describe'  : videoInstance['describe'],
			'Tag'       : videoInstance['tag'],
			'AddrStr'	: videoInstance['lbs_addr'],
			'Longitude'	: videoInstance['lbs_lon'],
			'Latitude'	: videoInstance['lbs_lat'],
			'Duration'  : videoInstance['duration'],
			'Published' : videoInstance['create_time'],
			'Definition': MediaProbe.definition(videoInstance['video_height']),
			'Poster'    : "%s/%s.jpg" % (PosterBaseURL, videoInstance['id']),
			'PosterURLs': ("%s/%s.jpg" % (PosterBaseURL, videoInstance['id']), ),
			'VideoURLs' : VideoURLs,
			'Videos'    : video_urls,
		}

	return None


def video_ready(data):
	"""
	视频处理状态
	方法：
		video_ready
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
	result = []
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()
	videoInstance = db.get('SELECT * FROM `video` WHERE `id` = %s', (data['VID']))
	if videoInstance:

		VideoBaseURL = Config.get('Video','VideoBaseURL')
		videoTranscodeListInstance = db.list('SELECT * FROM `video_transcode` WHERE `video_id` = %s ORDER BY `video_width` DESC', (data['VID']))

		for videoTranscodeInstance in videoTranscodeListInstance:
			result.append({
				'Definition': MediaProbe.definitionName(videoTranscodeInstance['video_height'], videoTranscodeInstance['video_width']),
				'Ready'     : videoTranscodeInstance['is_ready'] == 1,
				'URL'       : "%s/%s" % (VideoBaseURL, videoTranscodeInstance['file_name']),
				'Progress'  : float(videoTranscodeInstance['progress']),
			})

	return result


def video_poster(data):
	"""
	视频截图更新
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
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()
	videoInstance = db.get('SELECT * FROM `video` WHERE `id` = %s', (data['VID']))

	if videoInstance:
		fileName = "%s/%s.mp4" % (videoDirectory, videoInstance['id'])

		PosterBaseURL = Config.get('Video','PosterBaseURL')
		PosterURL = "%s/%s.jpg" % (PosterBaseURL, videoInstance['id'])

		Transcoder.VideoPoster(fileName, ("%s/%s.jpg" % (videoDirectory, videoInstance['id'])), ss=float(data['Time']))
		return {
			'VID'       : videoInstance['id'],
			'Poster'    : PosterURL
		}

	return None


def video_remove(data):
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
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()

	videoInstance = db.get('SELECT * FROM `video` WHERE `owner_id`=%s and `id` = %s', (userId, data['VID']))
	if not videoInstance:
		raise Exception("视频不存在.")

	db.delete("DELETE FROM `video` WHERE `owner_id`=%s and `id` = %s", (userId, data['VID']))
	db.end()

	return {'VID': data['VID']}





