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
	pass

def space_res_unrelation(data):
	pass

def space_res_order(data):
	pass

def space_res_list(data):
	pass

def space_authorize(data):
	pass

def space_authorize_list(data):
	pass

def space_authorized_spaces(data):
	pass

def space_authorized_resources(data):
	pass


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
