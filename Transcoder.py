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

	@staticmethod
	def videoGeneratePoster(fileName):
		destFileName, fileExtension = os.path.splitext(fileName)
		media = MediaProbe(fileName)
		duration = int(media.duration())
		for i in range(0,5):
			ss = float(duration * i) / 5
			if not Transcoder.VideoPoster(fileName, str(i), duration * i / 5):
				return False

		return True

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

	def __init__(self, settings, task=None):
		if not settings.has_key('file') or not settings.has_key('output'):
			raise ValueError, 'settings'

		threading.Thread.__init__(self)
		self._task = task
		self._settings = settings
		self._processed = 0
		self._started = False
		self._isfinished = False
		self._keepaspect = True

		self._probe = MediaProbe(self._settings['file'])



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
				times = re.findall(r"time=([\d+|\.]+?)\s", line)
				if len(times) > 0:
					self._started = True
					self._processed = float(times[0])

			if self.subp.poll() != None:
				self._isfinished = True
				break # finished



if __name__ == '__main__':
	import sys

	if len(sys.argv) < 2:
		raise ValueError, 'Need <input> file and <output> file'

	w = Worker({'file': sys.argv[1],
				'output': sys.argv[2]})
	w.start()

	while True:
		if not w.isProcessing():
			if w.hasError():
				print 'has error!!!'
			break

		print w.progress()
		w.join(1)

	print w.isFinished()
