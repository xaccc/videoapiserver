#!/usr/bin/env python
#coding=utf-8
import subprocess, threading, time, multiprocessing
import re, os, signal
import commands, uuid, json

from datetime import datetime
from MediaProbe import MediaProbe
from ConfigParser import ConfigParser
from MySQL import MySQL


applicationConfig = ConfigParser()
applicationConfig.read('Config.ini')


def enum(**enums):
	return type('Enum', (), enums)


TaskStatus = enum(QUEUE='排队中', RUN='转码中', FINISHED='转码完成', ERROR='转码失败')


TranscodeTemplates = enum(
	QCIF = {
			'video_codec'	: 'libx264 -profile:v baseline -level 12',
			'video_bitrate'	: 90*1024,
			'video_width'	: 160,
			'audio_codec'	: 'aac -strict -2',
			'audio_channel'	: 1,
			'audio_bitrate'	: 16*1024,
			},
	CIF = {
			'video_codec'	: 'libx264 -profile:v baseline -level 12',
			'video_bitrate'	: 150*1024,
			'video_width'	: 320,
			'audio_codec'	: 'aac -strict -2',
			'audio_channel'	: 1,
			'audio_bitrate'	: 24*1024,
			},
	SD = {
			'video_codec'	: 'libx264 -profile:v baseline -level 12',
			'video_bitrate'	: 400*1024,
			'video_width'	: 640,
			'audio_codec'	: 'aac -strict -2',
			'audio_channel'	: 1,
			'audio_bitrate'	: 32*1024,
			},
	HD = {
			'video_codec'	: 'libx264 -profile:v baseline -level 21',
			'video_bitrate'	: 800*1024,
			'video_width'	: 1280,
			'audio_codec'	: 'aac -strict -2',
			'audio_channel'	: 1,
			'audio_bitrate'	: 64*1024,
			},
	HDPRO = {
			'video_codec'	: 'libx264 -profile:v baseline -level 21',
			'video_bitrate'	: 2*1024*1024,
			'video_width'	: 1920,
			'audio_codec'	: 'aac -strict -2',
			'audio_channel'	: 2,
			'audio_bitrate'	: 128*1024,
			},
	)



class Transcoder(object):

	__workers = []
	__lock = threading.Lock()

	def __init__(self, Started = None, Progress = None, Finished = None, Error = None):
		self.__cb_Start = Started
		self.__cb_Progress = Progress
		self.__cb_Finished = Finished
		self.__cb_Error = Error

	def addTask(self, settings, arg = None):
		worker = Worker(settings = settings, mgr = self, arg = arg)

		Transcoder.__lock.acquire()
		Transcoder.__workers.append(worker)
		if len(Transcoder.__workers) == 1:
			worker.start()
		Transcoder.__lock.release()
		pass

	def Count(self):
		return len(Transcoder.__workers)

	def worker_started(self, worker, arg):
		if self.__cb_Start:
			self.__cb_Start(arg)

	def worker_progress(self, worker, arg, percent, fps):
		if self.__cb_Progress:
			self.__cb_Progress(arg, percent, fps)

	def worker_finished(self, worker, arg):
		Transcoder.__lock.acquire()
		Transcoder.__workers.remove(worker)
		if len(Transcoder.__workers) > 0:
			Transcoder.__workers[0].start()
		Transcoder.__lock.release()

		if self.__cb_Finished:
			self.__cb_Finished(arg)


	def worker_error(self, worker, arg):
		Transcoder.__lock.acquire()
		Transcoder.__workers.remove(worker)
		if len(Transcoder.__workers) > 0:
			Transcoder.__workers[0].start()
		Transcoder.__lock.release()

		if self.__cb_Error:
			self.__cb_Error(arg)


	@staticmethod
	def videoGeneratePoster(fileName):
		destFileName, fileExtension = os.path.splitext(fileName)
		media = MediaProbe(fileName)
		duration = int(media.duration())

		return Transcoder.VideoPoster(fileName)

	@staticmethod
	def VideoPoster(fileName, destFileName = None, ss = None):
		if ss == None:
			media = MediaProbe(fileName)
			duration = int(media.duration())
			ss = float(duration) / 5

		if destFileName == None:
			destFileName, fileExtension = os.path.splitext(fileName)
			destFileName += '.jpg'

		code, text = commands.getstatusoutput('avconv -ss %s -i %s -map_metadata -1 -vframes 1 -y "%s"' % (str(ss), fileName, destFileName))
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
			


class Worker(threading.Thread):

	def __init__(self, settings, mgr=None, arg=None):
		"""
		settings: {
				'file'
				'video_codec'
				'video_bitrate'
				'video_width'
				'video_height'
				'audio_codec'
				'audio_channels'
				'audio_bitrate'
				'format'
				'output'
			}
		"""
		if not settings.has_key('file') or not settings.has_key('output'):
			raise ValueError, 'settings'

		threading.Thread.__init__(self)
		self._mgr = mgr
		self._arg = arg
		self._settings = settings
		self._progress = 0
		self._fps = 0
		self._started = False
		self._isfinished = False
		self._keepaspect = True

		self._probe = MediaProbe(self._settings['file'])

	def fps(self):
		return self._fps

	def settings(self):
		return self._settings

	def progress(self):
		return self._progress / self._probe.duration() if not self._isfinished else 1 if self._started else -1

	def hasError(self):
		return (not self._started) and self._isfinished

	def isProcessing(self):
		return threading.Thread.isAlive(self)

	def isStarted(self):
		return self._started

	def isFinished(self):
		return self._isfinished

	def keepAspect(self, keep=None):
		if keep != None:
			self._keepaspect = bool(keep)

		return self._keepaspect


	def createSubProecess(self):
		command = []

		# input
		command.append('avconv')
		command.append('-i "%s" -map_metadata -1' % self._settings['file'])

		# video settings
		if self._settings.get('video_codec') == 'copy':
			command.append('-vcodec copy')
		elif self._settings.get('video_codec') == 'none':
			command.append('-vn')
		else:
			command.append('-vcodec')
			command.append(str(self._settings.get('video_codec', 'libx264 -profile:v baseline -level 21')))
			command.append('-b:v')
			command.append(str(self._settings.get('video_bitrate', '150k')))
			command.append('-s')
			command.append(str(self._settings.get('video_size', '%ix%i' % (
						int(self._settings.get('video_width', 320)),
						int(self._settings.get('video_width', 320)/self._probe.videoAspect() if self.keepAspect() else self._settings.get('video_height', 240))
						))))

		# audio settings
		if self._settings.get('audio_codec') == 'copy':
			command.append('-acodec copy')
		elif self._settings.get('audio_codec') == 'none':
			command.append('-an')
		else:
			command.append('-acodec')
			command.append(str(self._settings.get('audio_codec', 'aac -strict -2')))
			command.append('-ac')
			command.append(str(self._settings.get('audio_channels', '1')))
			command.append('-b:a')
			command.append(str(self._settings.get('audio_bitrate', '32k')))

		# output settings
		command.append('-f')
		command.append(str(self._settings.get('format', 'mp4')))
		command.append('-y "%s"' % self._settings['output'])

		return subprocess.Popen(' '.join(command),
				stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, close_fds=True)


	def run(self):

		self.subp = self.createSubProecess()
		
		buf = ''
		while True:
			while True: #read output
				readed = self.subp.stderr.read(1)
				if not readed or len(readed) == 0:
					break; # don't read anything

				buf += readed
				if 'bits/s' in buf:
					#process line
					line = buf[0:buf.index('bits/s')+6]
					buf = buf[len(line):]
					times = re.findall(r"time=\s*([\d+|\.]+?)\s", line)
					if len(times) > 0:
						if not self._started and self._mgr:
							self._mgr.worker_started(self, self._arg)

						self._started = True
						self._progress = float(times[0])

					fps = re.findall(r"fps=\s*([\d+|\.]+?)\s", line)
					if len(fps) > 0:
						self._fps = float(fps[0])

					if self._mgr != None:
						self._mgr.worker_progress(self, self._arg, self.progress(), self._fps)

			if self.subp.poll() != None:
				self._isfinished = True
				if self._mgr != None:
					if self._started:
						self._mgr.worker_finished(self, self._arg)
					else:
						self._mgr.worker_error(self, self._arg)
				break; # subprocess exit!!!


__shutdown = threading.Event()

def sig_handler(sig, frame):
	print 'shutdown ...'
	__shutdown.set()


def __Started(transcodeId):
	db = MySQL()
	db.update("UPDATE `video_transcode` set `transcode_time` = now(), `progress` = 0 WHERE `id` = %s", (transcodeId))
	db.end()
	print "[%s] [Start] %s ..." % (datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), transcodeId)
	pass

def __Progress(transcodeId, percent, fps):
	db = MySQL()
	db.update("UPDATE `video_transcode` set `update_time` = now(), `progress` = %s WHERE `id` = %s", (float(percent), transcodeId))
	db.end()
	pass

def __Finished(transcodeId):
	print "[%s] [Finished] %s ..." % (datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), transcodeId)
	db = MySQL()
	db.update("UPDATE `video_transcode` set `is_ready` = 1, `progress` = 1 WHERE `id` = %s", (transcodeId))
	db.end()
	pass

def __Error(transcodeId):
	print "[%s] [Error] %s ..." % (datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), transcodeId)
	pass


def StartTranscodeService():
	import socket
	hostname = socket.gethostname()

	pid = os.getpid()

	f = open('transcoder.pid', 'wb')
	f.write(str(pid))
	f.close()

	signal.signal(signal.SIGTERM, sig_handler)
	signal.signal(signal.SIGINT, sig_handler)

	db = MySQL()
	transcoder = Transcoder(Started = __Started, Progress = __Progress, Finished = __Finished, Error = __Error)
	uploadDirectory = applicationConfig.get('Server','Upload')
	videoDirectory = applicationConfig.get('Video','SavePath')
	if not os.path.exists(videoDirectory):
		os.makedirs(videoDirectory)
	

	while True:
		if __shutdown.wait(1):
			break; # exit thread

		if transcoder.Count() > 0:
			continue; # wait process

		taskList = db.list('SELECT * FROM `video_transcode` WHERE `transcoder` IS NULL ORDER BY `id` LIMIT 0,1 FOR UPDATE')

		for task in taskList:
			db.update("UPDATE `video_transcode` set `transcoder` = %s WHERE `id` = %s", (hostname, task['id']))
			db2 = MySQL()
			videoInstance = db2.get("SELECT * FROM `video` WHERE `id`=%s", (task['video_id']))

			if videoInstance:
				fileName = "%s/%s" % (uploadDirectory, videoInstance['upload_id'])
				destFileName = "%s/%s" % (videoDirectory, task['file_name'])
				transcoder.addTask({
					'file' 			: fileName,
					'video_codec'	: task['video_codec'],
					'video_bitrate'	: task['video_bitrate'],
					'video_width'	: task['video_width'],
					'video_height'	: task['video_height'],
					'audio_codec'	: task['audio_codec'],
					'audio_channels': task['audio_channels'],
					'audio_bitrate'	: task['audio_bitrate'],
					'output'		: destFileName,
					}, arg = task['id'])

		db.end()

	while transcoder.Count() > 0:
		theading.sleep(1)
		print '.'


if __name__ == '__main__':
	import sys

	if len(sys.argv) >= 2:
		def xxx(file, percent, fps):
			print "[%s] complete: %s, fps: %s" % (file, percent, fps)
		def xxx2(file):
			print "[%s] completed!" % (file)

		transcoder = Transcoder(Progress = xxx, Finished=xxx2)
		transcoder.addTask({'file': sys.argv[1],
							'output': sys.argv[2]}, sys.argv[1])
	else:
		StartTranscodeService()




