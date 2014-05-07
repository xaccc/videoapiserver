#coding=utf-8
#-*- encoding: utf-8 -*-

from ConfigParser import ConfigParser

applicationConfig = ConfigParser()
applicationConfig.read('Config.ini')

def set(section, option, value):
	applicationConfig.set(section, option, value)

def get(section, option):
	return applicationConfig.get(section, option)

def getint(section, option):
	return applicationConfig.getint(section, option)	

def getfloat(section, option):
	return applicationConfig.getfloat(section, option)	

def getboolean(section, option):
	return applicationConfig.getboolean(section, option)	
