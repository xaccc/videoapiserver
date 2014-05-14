#coding=utf-8
#-*- encoding: utf-8 -*-

from datetime import datetime, timedelta
from MySQL import MySQL
from random import randint

import Config
import Utils
import UserService


__create_table_script = """
CREATE TABLE IF NOT EXISTS `space` (
  `id` char(32) COLLATE utf8_bin NOT NULL,
  `user_id` char(32) COLLATE utf8_bin NOT NULL,
  `name` varchar(100) COLLATE utf8_bin NOT NULL,
  `index` int(11) NOT NULL DEFAULT '0',
  `create_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE IF NOT EXISTS `space_authorize` (
  `space_id` char(32) COLLATE utf8_bin NOT NULL,
  `user_id` char(32) COLLATE utf8_bin NOT NULL,
  `allow_edit` tinyint(1) NOT NULL DEFAULT '0',
  KEY `space_id` (`space_id`,`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE IF NOT EXISTS `space_resource` (
  `id` char(32) COLLATE utf8_bin NOT NULL,
  `space_id` char(32) COLLATE utf8_bin NOT NULL,
  `owner_id` char(32) COLLATE utf8_bin NOT NULL,
  `res_type` varchar(20) COLLATE utf8_bin NOT NULL,
  `res_id` char(20) COLLATE utf8_bin NOT NULL,
  `order_field1` int(11) DEFAULT NULL,
  `order_field2` int(11) DEFAULT NULL,
  `order_field3` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `space_id` (`space_id`)
  KEY `res_id` (`res_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
"""


def space_list(data):
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()

	spaceListInstance = db.list('SELECT * FROM `space` WHERE `user_id` = %s ORDER BY `index`', (userId))
	
	results = []
	for space in spaceListInstance:
		results.append({
				'Id': space['id'],
				'Name': space['name'],
			})

	return {
		'Count': len(results),
		'Spaces': results,
	}


def space_create(data):
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()

	spaceId = Utils.UUID()
	result = db.save("INSERT INTO `space` (`id`, `user_id`, `name`) VALUES (%s,%s,%s)", 
					(spaceId, userId, data.get('Name', '')))
	db.end()

	space_reindex({
			'UserKey': data['UserKey'],
			'Id': spaceId,
			'After': data.get('After', ''),
		})

	return {
		'Id': spaceId,
		'Name': data.get('Name', '')
	}


def space_reindex(data):
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()

	spaceId = data.get('Id', '')
	afterId = data.get('After', '')

	index = []
	spaceListInstance = db.list('SELECT * FROM `space` WHERE `user_id` = %s ORDER BY `index`', (userId))
	for space in spaceListInstance:
		index.append(space['id'])

	if not spaceId in index:
		raise Error('空间不存在')

	index.remove(spaceId)
	if afterId == 'HEAD':
		index.insert(0, spaceId)
	elif afterId in index:
		index.insert(index.index(afterId) + 1, spaceId)
	else:
		index.append(spaceId)

	for i,value in enumerate(index):
		db.update("UPDATE `space` SET `index` = %s WHERE `id` = %s", (i, value))
	db.end()

	return {
		'Id': spaceId,
	}


def space_rename(data):
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()
	result = db.update("UPDATE `space` SET `name` = %s WHERE `id` = %s AND `user_id` = %s", (data.get('Name', ''), data.get('Id', ''), userId))
	db.end()

	if result > 0:
		return {
			'Id': data.get('Id', ''),
			'Name': data.get('Name', ''),
		}
	else:
		raise Error('更新失败或空间不存在')


def space_res_relation(data):
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()
	
	# TEST AUTHORIZE
	if __test_auth_edit(userId, data.get('Id', '')) > 0:
		newId = Utils.UUID()
		result = db.update("INSERT INTO `space_resource` (`id`, `space_id`, `owner_id`, `res_type`, `res_id`, `order_field1`, `order_field2`, `order_field3`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", 
						(newId, data.get('Id', ''), userId, data.get('ResType', ''), data.get('ResId', ''), data.get('OrderField1', None), data.get('OrderField2', None), data.get('OrderField3', None)))
		db.end()

		if result > 0:
			return {
				'Id': data.get('Id', ''),
				'ResType': data.get('ResType', ''),
				'ResId': data.get('ResId', ''),
			}
		else:
			raise Error('更新失败或空间不存在')
	else:
		raise Error('没有权限或空间不存在')


def space_res_unrelation(data):
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()
	
	# TEST AUTHORIZE
	if __test_auth_edit(userId, data.get('Id', '')) > 0:
		result = db.delete("DELETE FROM `space_resource`  WHERE `space_id`=%s AND `res_type`=%s AND `res_id`=%s", 
						(data.get('Id', ''), data.get('ResType', ''), data.get('ResId', '')))
		db.end()
		if result > 0:
			return {
				'Id': data.get('Id', ''),
				'ResType': data.get('ResType', ''),
				'ResId': data.get('ResId', ''),
			}
		else:
			raise Error('删除失败或资源不存在')
	else:
		raise Error('没有权限或空间不存在')


def space_res_order(data):
	userId = UserService.user_id(data['UserKey'])
	db = MySQL()
	
	# TEST AUTHORIZE
	if __test_auth_edit(userId, data.get('Id', '')) > 0:
		newId = Utils.UUID()
		result = db.update("UPDATE `space_resource` SET `order_field1`=%s, `order_field2`=%s, `order_field3`=%s WHERE `space_id`=%s AND `res_type`=%s AND `res_id`=%s", 
						(data.get('OrderField1', None), data.get('OrderField2', None), data.get('OrderField3', None), data.get('Id', ''), userId, data.get('ResType', ''), data.get('ResId', '')))
		db.end()

		if result > 0:
			return {
				'Id': data.get('Id', ''),
				'ResType': data.get('ResType', ''),
				'ResId': data.get('ResId', ''),
			}
		else:
			raise Error('更新失败或空间不存在')
	else:
		raise Error('没有权限或空间不存在')

def space_res_list(data):
	userId = UserService.user_id(data['UserKey'])
	if __test_auth_view(userId, data.get('Id', '')) > 0:
		offset = long(data.get('Offset', 0))
		sort = max(1, min(3, int(data.get('Sort', 1))))
		order = int(data.get('Order', 0))
		listMax = min(100, data.get('Max', 10))
		resCount = db.get("SELECT COUNT(*) AS c FROM `space_resource` WHERE `space_id` = %s AND `res_type`=%s", (data.get('Id', ''), data.get('ResType', '')))['c']
		resList = db.list("SELECT * FROM `space_resource` WHERE `space_id` = %s AND `res_type`=%s ORDER BY `order_field" + str(sort) + "` %s LIMIT %s,%s", 
							(data.get('Id', ''), data.get('ResType', ''), 'ASC' if order == 0 else 'DESC', offset, listMax))
		results = []
		for res in resList:
			results.append({
					'ResId': res['res_id'],
					'OrderField1': res['order_field1'],
					'OrderField2': res['order_field2'],
					'OrderField3': res['order_field3'],
				})

		return {
			'Id': data.get('Id', ''),
			'ResType': data.get('ResType', ''),
			'Count': resCount,
			'Offset': offset,
			'Max': listMax,
			'Sort': sort,
			'Order': order,
			'Results': results,
		}
	else:
		raise Error('没有权限或空间不存在')


def space_authorize(data):
	userId = UserService.user_id(data['UserKey'])
	spaceInstance = space_get(data.get('Id', ''))
	if userId == spaceInstance['user_id']:
		allowEdit = min(1, max(0, int(data.get('AllowEdit', 0))))
		db = MySQL()
		authorizeUser = UserService.user_get(data.get('UserId', ''))
		result = db.update("REPLACE INTO `space_authorize` (`space_id`, `user_id`, `allow_edit`) VALUES (%s,%s,%s)", 
						(data.get('Id', ''), data.get('UserId', ''), allowEdit))
		db.end()
		return {
			'Id': spaceInstance['id'],
			'Name': spaceInstance['name'],
			'UserId': authorizeUser['id'],
			'UserName': authorizeUser['name'],
			'AllowEdit': allowEdit,
		}
	else:
		raise Error('没有权限或空间不存在')


def space_unauthorize(data):
	userId = UserService.user_id(data['UserKey'])
	spaceInstance = space_get(data.get('Id', ''))
	if userId == spaceInstance['user_id']:
		db = MySQL()
		result = db.delete("DELETE FROM `space_authorize` WHERE `space_id`=%s AND `user_id`=%s", 
						(data.get('Id', ''), data.get('UserId', ''), allowEdit))
		db.end()
		if result > 0:
			return {
				'Id': data.get('Id', ''),
				'UserId': data.get('UserId', ''),
			}
		else:
			raise Error('删除失败或授权不存在')
	else:
		raise Error('没有权限或空间不存在')


def space_authorize_list(data):
	userId = UserService.user_id(data['UserKey'])
	spaceInstance = space_get(data.get('Id', ''))

	if userId == spaceInstance['user_id']:
		db = MySQL()
		results=[]
		for item in db.list("SELECT DISTINCT * FROM `space_authorize` WHERE `space_id`=%s", data.get('Id', '')):
			authorizeUser = UserService.user_get(item['user_id'])
			results.append({
					'UserId': item['user_id'],
					'UserName': authorizeUser['name'],
					'AllowEdit': item['allow_edit']
				})
		return {
			'Id': data.get('Id', ''),
			'Name': spaceInstance['name'], 
			'Results': results
		}
	else:
		raise Error('没有权限或空间不存在')


def space_authorized_spaces(data):
	userId = UserService.user_id(data['UserKey'])
	userInstance = UserService.user_get(userId)

	db = MySQL()
	results=[]
	for item in db.list("SELECT DISTINCT * FROM `space_authorize` WHERE `user_id`=%s", userId):
		spaceInstance = space_get(item['space_id'])
		spaceOwner = UserService.user_get(item['user_id'], notRaise=True)
		results.append({
				'Id': spaceInstance['id'],
				'Name': spaceInstance['name'],
				'Owner': spaceOwner['name'] if spaceOwner else None,
				'OwnerId': item['user_id'],
				'AllowEdit': item['allow_edit']
			})

	return results


def space_authorized_resources(data):
	pass



def space_get(spaceId):
	return MySQL().get("SELECT * FROM `space` WHERE `id` = %s", spaceId)



def __test_auth_edit(userId, spaceId):
	db = MySQL()
	authorized = 0
	
	# TEST AUTHORIZE
	spaceInstance = db.get('SELECT * FROM `space` WHERE `id` = %s', (spaceId))
	if spaceInstance:
		if userId == spaceInstance['user_id']:
			authorized = 1
		else:
			authorized = db.get('SELECT COUNT(*) AS c FROM `space_authorize` WHERE `space_id`=%s AND `user_id` = %s AND `allow_edit` = 1', (data.get('Id', ''), userId))['c']
	else:
		authorized = -1

	return authorized


def __test_auth_view(userId, spaceId):
	db = MySQL()
	authorized = 0
	
	# TEST AUTHORIZE
	spaceInstance = db.get('SELECT * FROM `space` WHERE `id` = %s', (spaceId))
	if spaceInstance:
		if userId == spaceInstance['user_id']:
			authorized = 1
		else:
			authorized = db.get('SELECT COUNT(*) AS c FROM `space_authorize` WHERE `space_id`=%s AND `user_id` = %s', (data.get('Id', ''), userId))['c']
	else:
		authorized = -1

	return authorized





if __name__ == '__main__':
	import sys, json

	if len(sys.argv) > 1:
		newSpace = space_create({
				'UserKey': sys.argv[1],
				'Name': '测试空间ABC'
			})

		print json.dumps(space_list({ 'UserKey': sys.argv[1] }),sort_keys=False,indent=4)

		space_reindex({
				'UserKey': sys.argv[1],
				'Id': newSpace['Id'],
				'After': 'HEAD',
			})

		print json.dumps(space_list({ 'UserKey': sys.argv[1] }),sort_keys=False,indent=4)

		space_rename({
				'UserKey': sys.argv[1],
				'Id': newSpace['Id'],
				'Name': 'test-123' + datetime.now().strftime('%H:%M:%S'),
			})
		print json.dumps(space_list({ 'UserKey': sys.argv[1] }),sort_keys=False,indent=4)

	for user in UserService.user_list():
		spaceList = space_list({ 'UserKey': user['id'] })
		if spaceList['Count'] == 0:
			# create default space
			newSpace = space_create({
					'UserKey': user['id'],
					'Name': '我的视光宝盒'
				})
