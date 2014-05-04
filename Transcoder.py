#coding=utf-8
import subprocess, threading, time, multiprocessing
import re, os
import commands, uuid, json

from MediaProbe import MediaProbe


cmd_conv = 'avconv'


def enum(**enums):
	return type('Enum', (), enums)


TaskStatus = enum(QUEUE='排队中', RUN='转码中', FINISHED='转码完成', ERROR='转码失败')


Templates = enum(
	QCIF = {
			'video_codec'	: 'libx264 -profile:v baseline -level 12',
			'video_bitrate'	: '90k',
			'video_width'	: '160',
			'audio_codec'	: 'aac -strict -2',
			'audio_channel'	: '1',
			'audio_bitrate'	: '16k',
			},
	CIF = {
			'video_codec'	: 'libx264 -profile:v baseline -level 12',
			'video_bitrate'	: '150k',
			'video_width'	: '320',
			'audio_codec'	: 'aac -strict -2',
			'audio_channel'	: '1',
			'audio_bitrate'	: '24k',
			},
	SD = {
			'video_codec'	: 'libx264 -profile:v baseline -level 12',
			'video_bitrate'	: '350k',
			'video_width'	: '640',
			'audio_codec'	: 'aac -strict -2',
			'audio_channel'	: '1',
			'audio_bitrate'	: '32k',
			},
	HD = {
			'video_codec'	: 'libx264 -profile:v baseline -level 21',
			'video_bitrate'	: '700k',
			'video_width'	: '1280',
			'audio_codec'	: 'aac -strict -2',
			'audio_channel'	: '1',
			'audio_bitrate'	: '32k',
			},
	HDPRO = {
			'video_codec'	: 'libx264 -profile:v baseline -level 21',
			'video_bitrate'	: '2000k',
			'video_width'	: '1920',
			'audio_codec'	: 'aac -strict -2',
			'audio_channel'	: '1',
			'audio_bitrate'	: '32k',
			},
	)



class Transcoder(object):

	workers = set()
	__lock = threading.Lock()

	def __init__(self):
		pass

	def addTask(self, settings, arg = None):
		worker = Worker(settings = settings, mgr = self, arg = arg)

		__lock.acquire()
		workers.add(worker)
		if len(workers) == 1:
			worker.start()
		__lock.release()
		pass

	def worker_list(self):
		pass
	def worker_started(self, worker, arg):
		pass
	def worker_progress(self, worker, arg, percent, fps):
		pass
	def worker_finished(self, worker, arg):
		__lock.acquire()
		workers.remove(worker)
		__lock.release()
		pass
	def worker_error(self, worker, arg):
		__lock.acquire()
		workers.remove(worker)
		if len(workers) > 0:
			workers[0].start()
		__lock.release()
		pass

	@staticmethod
	def videoGeneratePoster(fileName):
		destFileName, fileExtension = os.path.splitext(fileName)
		media = MediaProbe(fileName)
		duration = int(media.duration())

		return Transcoder.VideoPoster(fileName, '1'):

	@staticmethod
	def VideoPoster(fileName, posterSuffix = '1', ss = None):
		if ss == None:
			media = MediaProbe(fileName)
			duration = int(media.duration())
			ss = float(duration) / 5

		destFileName, fileExtension = os.path.splitext(fileName)
		posterFileName = "%s_%s.jpg" % (destFileName, str(posterSuffix))

		code, text = commands.getstatusoutput('avconv -ss %s -i %s -map_metadata -1 -vframes 1 -y "%s"' % (str(ss), fileName, posterFileName))
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
		return self._processed / self._probe.duration() if not self._isfinished else 1 if self._started else -1

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


	def run(self):

		self.subp = subprocess.Popen('%s -i "%s" -vcodec %s -b:a %s -s %s -acodec %s -ac %s -b:a %s -f %s -y "%s"' % (
				cmd_conv,
				self._settings['file'],
				self._settings.get('video_codec', 'libx264 -profile:v baseline -level 21'),
				self._settings.get('video_bitrate', '150k'),
				self._settings.get('video_size', '%ix%i' % (
					int(self._settings.get('video_width', 320)),
					int(self._settings.get('video_width', 320)/self._probe.videoAspect() if self.keepAspect() else self._settings.get('video_height', 240))
					)),
				self._settings.get('audio_codec', 'aac -strict -2'),
				self._settings.get('audio_channel', '1'),
				self._settings.get('audio_bitrate', '32k'),
				self._settings.get('format', 'mp4'),
				self._settings['output']),
				stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, close_fds=True)
		
		buf = ''
		while True:
			buf += self.subp.stderr.read(1)
			if 'bits/s' in buf:
				#process line
				line = buf[0:buf.index('bits/s')+6]
				buf = buf[len(line):]
				times = re.findall(r"time=\s*([\d+|\.]+?)\s", line)
				if len(times) > 0:
					if self._mgr != None:
						self._mgr.worker_started(self, self._arg)

					self._started = True
					self._progress = float(times[0])

				fps = re.findall(r"fps=\s*([\d+|\.]+?)\s", line)
				if len(fps) > 0:
					self._fps = float(fps[0])

				if self._mgr != None:
					self._mgr.worker_processe(self, self._arg, self._progress, self._fps)

			if self.subp.poll() != None:
				self._isfinished = True
				if self._mgr != None:
					if self._started:
						self._mgr.worker_finished(self, self._arg)
					else:
						self._mgr.worker_error(self, self._arg)
				break # finished



if __name__ == '__main__':
	import sys

	if len(sys.argv) < 2:
		raise ValueError, 'Need <input> file and <output> file'

	transcoder = Transcoder()
	transcoder.addTask({'file': sys.argv[1],
				'output': sys.argv[2]})

	while True:
		if not w.isProcessing():
			if w.hasError():
				print 'has error!!!'
			break

		print "percent: %s, FPS: %s" % (w.progress(), w.fps())
