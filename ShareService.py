#coding=utf-8
#-*- encoding: utf-8 -*-

from datetime import datetime, timedelta
from MySQL import MySQL

import Config
import Utils
import UserService, NotifyService

def share_video(data):
	"""
	分享视频
	方法：
		share_video
	参数：
		UserKey[string] –用户登录后的会话ID。
		VID[string] – 分配的视频ID
		To[Array] – 分享对象列表，分享对象如下定义：
			Mobile[string] – 分享手机号，必填
			Name[string] – 分享姓名，可选
	返回值：
		sessionId[string] – 分配的分享会话ID
		Results[Array] – 分享结果对象列表，分享结果对象如下定义：
			Mobile[string] – 分享手机号
			Signup[boolean] – 是否注册用户
	"""
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()

	videoInstance = db.get('SELECT * FROM `video` WHERE `id` = %s', (data['VID']))
	if not videoInstance:
		raise Exception("视频不存在.")

	sessionId = Utils.UUID()
	results = []
	for to in data.get('To', ()):
		toUserId = UserService.getUserIdByMobile(to.get('Mobile'))
		result = db.save("""INSERT INTO `share` (`session_id`,`owner_id`,`video_id`,`to_user_id`,`to_mobile`,`to_name`) VALUES (%s,%s,%s,%s,%s,%s)"""
					, (sessionId, userId, data['VID'], toUserId, to.get('Mobile'), to.get('Name')))
		db.end()

		if toUserId:
			# create app notify
			NotifyService.create(toUserId, Utils.json_dumps({
				'Type'	: 'share_video',
				'From'	: UserService.user_mobile(userId),
				'To'	: to.get('Mobile'),
				'Date'	: datetime.now(),
				'VID'	: data['VID'],
			}), sender = 'share_video', refId = sessionId)

		if result:
			results.append({
				'Mobile': to.get('Mobile'),
				'Signup': toUserId != None
				})

	return {'SessionId': sessionId, 'Results': results}


def share_list(data):
	"""
	获取分享列表
	方法：
		share_list
	参数：
		UserKey[string] –用户登录后的会话ID。
		Offset[long] – 列表起始位置。
		Max[long] – 列表最大条数
	返回值：
		Count[long] – 列表数量（全部）
		Offset[long] – 列表起始位置。
		Max[long] – 列表最大条数
		Results[Array] – 视频对象列表，视频对象定义如下：
			to_time[date] – 创作日期
			to_name[date] – 分享日期
			VID[string] – 视频ID
	"""
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()

	offset = data.get('Offset', 0)
	listMax = min(100, data.get('Max', 10))
	count = long(db.get('SELECT COUNT(*) as c FROM `share_list` WHERE (`owner_id` = %s and flag=0) or (`to_user_id` = %s and flag = 1)', (userId,userId)).get('c'))

	results = []

	shareListInstance = db.list('SELECT * FROM `share_list` WHERE (`owner_id` = %s and flag=0) or (`to_user_id` = %s and flag = 1) ORDER BY `to_time` DESC LIMIT %s,%s', (userId, userId, offset, listMax))

	for shareInstance in shareListInstance:
		results.append({
			'ToTime'    : shareInstance['to_time'],
			'ToName'    : shareInstance['to_name'],
			'VID'       : shareInstance['video_id'],
			'Flag'      : shareInstance['flag'],
		})

	return {
		'Count'     : count,
		'Offset'    : offset,
		'Max'       : listMax,
		'Results'   : results,
	}





