#coding=utf-8
#-*- encoding: utf-8 -*-

from datetime import datetime, timedelta
from MySQL import MySQL
from random import randint

import Config
import Utils
import UserService


def invite_code(data):
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()

	code = Utils.UUID()
	result = db.save("INSERT INTO `invite` (`id`, `user_id`, `type`, `refer_id`, `info`) VALUES (%s,%s,%s,%s,%s)", 
					(code, userId, data.get('Type', None), data.get('ReferId', None), data.get('Info', None)))
	db.end()

	return {
		'Code': code,
	}


def invite_list(data):
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()

	inviteListInstance = db.list('SELECT * FROM `invite` WHERE `invite_date` >= NOW() - INTERVAL 60 DAY AND `is_pocket` <> 1 AND `user_id` = %s AND `type` = %s', (userId, data.get('Type', None)), sort='invite_date', order='DESC')
	
	results = []
	for invite in inviteListInstance:
		dealUser = UserService.user_get(invite['deal_user_id'], notRaise = True) if invite['deal_user_id'] else None
		results.append({
				'Code': invite['id'],
				'InviteDate': invite['invite_date'],
				'ReferId': invite['refer_id'],
				'IsDeal': invite['is_deal'],
				'DealUserId': invite['deal_user_id'] if dealUser else None,
				'DealUser': dealUser['name'] if dealUser else None,
				'DealDate': invite['deal_date'] if dealUser else None,
				'IsPocket': invite['is_pocket'],
				'PocketDate': invite['pocket_date'],
			})

	return {
		'Type': data.get('Type', None),
		'Count': len(results),
		'Results': results,
	}


def invite_pocket(data):
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()
	result = db.update("UPDATE `invite` SET `is_pocket` = 1, `pocket_date` = now() WHERE `user_id` = %s AND `id` = %s AND `is_pocket` <> 1", (userId, data.get('Code', None)))
	db.end()
	if result > 0:
		return {
			'Code': data.get('Code', None)
		}
	else:
		raise Error('邀请码不存在或已处理')


def invite_info(data):
	"""
	邀请信息
	参数：
		Code[string] – 邀请码
	返回值：
		Code[string] – 邀请码
		Type[string] - 邀请类型
		ReferId[string] - 引用对象ID
		InviterId[string] – 邀请者UserId
		Inviter[string] – 邀请者姓名
		InviteDate[date] – 邀请日期
		Info[string] – 邀请信息
	"""
	db = MySQL()

	invite = db.get('SELECT * FROM `invite` WHERE `id` = %s', (data.get('Code', None)))

	if not invite:
		raise Error('邀请码不存在')

	inviter = UserService.user_get(invite['user_id'], notRaise = True)
	dealUser = UserService.user_get(invite['deal_user_id'], notRaise = True) if invite['deal_user_id'] else None

	return {
			'Code': invite['id'],
			'Type': invite['type'],
			'Inviter': inviter['name'],
			'InviterId': invite['user_id'],
			'InviteDate': invite['invite_date'],
			'ReferId': invite['refer_id'],
			'IsDeal': invite['is_deal'],
			'DealUser': dealUser['name'] if dealUser else None,
			'DealUserId': invite['deal_user_id'] if dealUser else None,
			'DealDate': invite['deal_date'] if dealUser else None,
			'IsPocket': invite['is_pocket'],
			'PocketDate': invite['pocket_date'] if invite['is_pocket'] else None,
			'Info': invite['info'],
		}



def invite_deal(data):
	"""
	接受邀请
	参数：
		UserKey[string] – 用户会话ID
		Code[string] – 邀请码
	返回值：
		Code[string] – 邀请码
	"""
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()
	result = db.update("UPDATE `invite` SET `is_deal` = 1, `deal_date` = now(), `deal_user_id` = %s WHERE `id` = %s AND `is_deal` <> 1", (userId, data.get('Code', None)))
	db.end()
	if result > 0:
		return {
			'Code': data.get('Code', None)
		}
	else:
		raise Error('邀请码不存在或已处理')



if __name__ == '__main__':
	pass



