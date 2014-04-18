#coding=utf-8
#-*- encoding: utf-8 -*-

from MediaProbe import MediaProbe

import os
import commands
import uuid
import json
import multiprocessing


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

	@staticmethod
	def start():
		pass

	@staticmethod
	def stop():
		pass

	@staticmethod
	def task(vid):
		pass

	@staticmethod
	def videoGeneratePoster(fileName):
		destFileName, fileExtension = os.path.splitext(fileName)
		media = MediaProbe(fileName)
		duration = int(media.duration())
		for i in range(0,5):
			ss = duration * i / 5
			code, text = commands.getstatusoutput('avconv -ss %d -i %s -map_metadata -1 -vframes 1 -y "%s"' % (ss, fileName, "%s_%d.jpg" % (destFileName,i+1)))
			if code != 0:
				return False

		return True

	@staticmethod
	def videoTransform(fileName, destFileName):
		"""
		从上传位置转移到视频位置，并根据需要进行转码
		"""
		media = MediaProbe(fileName)

		vcodec = 'copy' if media.videoCodec() == 'h264' else 'libx264 -b:v %d' % media.videoBitrate()
		acodec = 'copy' if media.audioCodec() == 'aac' else 'aac -strict -2 -b:a %d' % media.audioBitrate()

		code, text = commands.getstatusoutput('avconv -v 0 -i "%s" -map_metadata -1 -vcodec %s -acodec %s -y "%s"' % (fileName, vcodec, acodec, destFileName))

		if code != 0:
			return False

		return Transcoder.videoGeneratePoster(destFileName)
			
if __name__ == "__main__":
	print Transcoder.videoTransform('./uploads/fc5540020456446a8cf341f141260fe1', './videos/fc5540020456446a8cf341f141260fe1.mp4')


