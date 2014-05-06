#!/usr/bin/env python
#coding=utf-8
#-*- encoding: utf-8 -*-

import os, shutil

from Transcoder import TranscodeTemplates
from ConfigParser import ConfigParser
from MediaProbe import MediaProbe
from MySQL import MySQL


print 'start to upgrade ...'



applicationConfig = ConfigParser()
applicationConfig.read('Config.ini')

uploadDirectory = applicationConfig.get('Server','Upload')
videoDirectory = applicationConfig.get('Video','SavePath')

db = MySQL()

videoList = db.list('SELECT * FROM `video`')

for video in videoList:
	print "convert %s <= %s" % (video['id'], video['upload_id'])

	# 视频文件地址
	srcFileName = "%s/%s.mp4" % (videoDirectory, video['upload_id'])
	destFileName = "%s/%s.mp4" % (videoDirectory, video['id'])

	if not os.path.exists(srcFileName):
		print '[文件被删除] vid: %s, upload_id: %s' % (video['id'], video['upload_id'])
		continue # 文件被删除

	os.rename(srcFileName, destFileName)

	# 截图文件地址
	srcPosterFileName = "%s/%s_0.jpg" % (videoDirectory, video['upload_id'])
	srcPoster1FileName = "%s/%s_1.jpg" % (videoDirectory, video['upload_id'])
	srcPoster2FileName = "%s/%s_2.jpg" % (videoDirectory, video['upload_id'])
	destPosterFileName = "%s/%s.jpg" % (videoDirectory, video['id'])
	if os.path.exists(srcPosterFileName):
		os.rename(srcPosterFileName, destPosterFileName)
	elif os.path.exists(srcPoster1FileName):
		os.rename(srcPoster1FileName, destPosterFileName)
	elif os.path.exists(srcPoster2FileName):
		os.rename(srcPoster2FileName, destPosterFileName)

	# 短地址库

	# 创建转码任务
	uploadFileName = "%s/%s" % (uploadDirectory, video['upload_id'])
	shutil.copyfile(destFileName, uploadFileName)

	newId = video['id']
	media = MediaProbe(uploadFileName)

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