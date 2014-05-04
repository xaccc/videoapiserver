#coding=utf-8
#-*- encoding: utf-8 -*-

import os
import sys
import commands
import uuid
import json
import multiprocessing


class MediaProbe(object):
	"""
	调用依赖的程序分析媒体文件的信息
	"""
	definitionName = ('流畅','标清(480p)','高清(720p)','超清(1080p)','4K')

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
		return self.__getFloat(self.videoStream, 'duration')

	def createTime(self):
		if self.format and self.format.has_key('tags') and self.format['tags'].has_key('creation_time'):
			return self.format['tags']['creation_time']
		else:
			return None

	@staticmethod
	def definition(height, width= 0):
		"""
		获取视频清晰度：0-流畅，1-标清，2-高清，3-超清，4-4K
		"""
		if height >= 2160 or width >= 3840:
			return 4
		elif height >= 1080 or width >= 1920:
			return 3
		elif height >= 720 or width >= 1280:
			return 2
		elif height >= 480 or width >= 640:
			return 1
		elif height >= 90 or width >= 120:
			return 0
		return -1

	@staticmethod
	def definitionName(height, width= 0):
		x = MediaProbe.definition(height, width)
		if x >= 0 and x < len(MediaProbe.definitionName):
			return MediaProbe.definitionName[x]
		return '未知清晰度'



if __name__ == "__main__":
	media = MediaProbe(sys.argv[1])
