#coding=utf-8
#-*- encoding: utf-8 -*-

from datetime import datetime, timedelta
from MySQL import MySQL

import Config
import Utils
import UserService
import NotifyTCPServer


def list(userId=None):
	db = MySQL()
	if userId:
		return db.list("SELECT * FROM `user_notify` WHERE `arrived` = 0 AND `user_id` = %s AND `create_date` >= NOW() - INTERVAL 7 DAY", (userId))
	else:
		return db.list("SELECT * FROM `user_notify` WHERE `arrived` = 0 AND `create_date` >= NOW() - INTERVAL 7 DAY")


def create(toUserId, notifyContent, sender=None, refId=None):
	notifyId = Utils.UUID()
	db = MySQL()
	db.save("INSERT INTO `user_notify` (`id`,`user_id`,`notify`,`sender`,`ref_id`) VALUES (%s,%s,%s,%s,%s)", (notifyId, toUserId, notifyContent, sender, refId))
	db.end()

	try:
		NotifyTCPServer.notify_server_has_new(toUserId)
	except Exception as e:
		print "Error: %s" % e

	return notifyId


def arrived(notifyId):
	db = MySQL()
	db.update("UPDATE `user_notify` SET `arrived_date` = NOW(), `arrived` = 1 WHERE `id` = %s", (notifyId))
	db.end()
