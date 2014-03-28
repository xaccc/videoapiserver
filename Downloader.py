#coding=utf-8
#-*- encoding: utf-8 -*-

import os
import sys
import commands
import uuid
import json
import multiprocessing
import logging

log = logging.getLogger('Downloader')

def Download(data):
    log.debug(json.dumps(data,sort_keys=False,indent=4))
    
    # script = 'avprobe -v 0 -of json -show_format -show_streams "%s"' % fileName
    # code, text = commands.getstatusoutput(script)
    # if code == 0:
    #     self.probe = json.loads(text)
    #     self.format = self.probe['format']
    #     self.videoStream = self.__stream('video')
    #     self.audioStream = self.__stream('audio')
    # else:
    #     print script
    #     print text
    #     raise Exception('不支持的文件类型或媒体探测模块安装有误！')



log.debug("startup downloader!")