# -*- encoding: utf-8 -*-

import MySQL

class Database(object):

	def __init__(self):
		self.db = MySQL({
						'host'	: 'localhost',
						'port'	: 3306,
						'user'	: 'root',
						'passwd': '1q2w3e',
						'db'	: 'videos'})
		pass

	def __del__(self):
		pass