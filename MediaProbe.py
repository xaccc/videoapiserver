#coding=utf-8
#-*- encoding: utf-8 -*-

import os, sys, commands
import uuid, json
import multiprocessing


class MediaProbe(object):
	"""
	调用依赖的程序分析媒体文件的信息
	"""
	_definitionName = ('流畅','标清','高清','超清','4K')

	def __init__(self, fileName):
		script = 'avprobe -v 0 -of json -show_format -show_streams "%s"' % fileName
		code, text = commands.getstatusoutput(script)
		if code == 0:
			jsonString = text[text.index('{'):] if text.index('{') >= 0 else '{}'
			self.probe = json.loads(jsonString.decode("utf-8", "replace"))
			self.format = self.probe['format']
			self.videoStream = self.__stream('video')
			self.audioStream = self.__stream('audio')
		else:
			print script
			print text
			raise Exception('不支持的文件类型或媒体探测模块安装有误！')


	def __stream(self, typeName):
		if self.probe.get('streams'):
			for stream in self.probe['streams']:
				if stream.get('codec_type') == typeName:
					return stream

		return None

	def __get(self, stream, key):
		return stream.get(key) if stream else None
	def __getFloat(self, stream, key):
		return float(stream.get(key, 0.0)) if stream else None
	def __getLong(self, stream, key):
		return long(float(stream.get(key, 0))) if stream else None
	def __getInt(self, stream, key):
		return int(float(stream.get(key, 0))) if stream else None

	def hasVideo(self):
		return self.videoStream != None
	def hasAudio(self):
		return self.audioStream != None

	def videoBitrate(self):
		return self.__getInt(self.videoStream, 'bit_rate')
	def audioChannels(self):
		return self.__getInt(self.audioStream, 'channels')
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
	def videoAspect(self):
		return float(self.videoWidth()) / float(self.videoHeight())
	def videoDefinition(self):
		return MediaProbe.definition(self.videoHeight(), self.videoWidth())

	def duration(self):
		try:
			return self.__getFloat(self.videoStream, 'duration')
		except:
			try:
				return self.__getFloat(self.format, 'duration')
			except:
				return -1

	def createTime(self):
		try:
			return self.format['tags']['creation_time']
		except:
			return None

	def supportSD(self):
		return MediaProbe.definition(self.videoHeight(), self.videoWidth()) >= 1
	def supportHD(self):
		return MediaProbe.definition(self.videoHeight(), self.videoWidth()) >= 2
	def supportHDpro(self):
		return MediaProbe.definition(self.videoHeight(), self.videoWidth()) >= 3

	def DefinitionIsSD(self):
		return MediaProbe.definition(self.videoHeight(), self.videoWidth()) == 1
	def DefinitionIsHD(self):
		return MediaProbe.definition(self.videoHeight(), self.videoWidth()) == 2
	def DefinitionIsHDpro(self):
		return MediaProbe.definition(self.videoHeight(), self.videoWidth()) == 3


	@staticmethod
	def definition(height, width = 0):
		"""
		获取视频清晰度：0-流畅，1-标清，2-高清，3-超清，4-4K
		"""
		if int(height) >= 2160 or int(width) >= 3840:
			return 4
		elif int(height) >= 1080 or int(width) >= 1920:
			return 3
		elif int(height) >= 720 or int(width) >= 1280:
			return 2
		elif int(height) >= 480 or int(width) >= 640:
			return 1
		elif int(height) >= 90 or int(width) >= 120:
			return 0
		return -1

	@staticmethod
	def definitionName(height, width=0):
		x = MediaProbe.definition(height, width)
		if x >= 0 and x < len(MediaProbe._definitionName):
			return MediaProbe._definitionName[x]
		return '未知清晰度'



if __name__ == "__main__":
	media = MediaProbe(sys.argv[1])
	print "videoBitrate : %s" % media.videoBitrate()
	print "audioChannels : %s" % media.audioChannels()
	print "audioBitrate : %s" % media.audioBitrate()
	print "videoCodec : %s" % media.videoCodec()
	print "audioCodec : %s" % media.audioCodec()
	print "videoWidth : %s" % media.videoWidth()
	print "videoHeight : %s" % media.videoHeight()
	print "videoAspect : %s" % media.videoAspect()
	print "videoDefinition : %s" % media.videoDefinition()
	print "duration : %s" % media.duration()
	print "createTime : %s" % media.createTime()
