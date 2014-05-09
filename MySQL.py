#coding=utf-8
#-*- encoding: utf-8 -*-
"""
desc:数据库操作类
@note:
1、执行带参数的ＳＱＬ时，请先用sql语句指定需要输入的条件列表，然后再用tuple/list进行条件批配
２、在格式ＳＱＬ中不需要使用引号指定数据类型，系统会根据输入参数自动识别
３、在输入的值中不需要使用转意函数，系统会自动处理
"""

import MySQLdb
import threading
import Config

from MySQLdb.cursors import DictCursor
from DBUtils.PooledDB import PooledDB


class MySQL(object):
	"""
		MYSQL数据库对象，负责产生数据库连接 , 此类中的连接采用连接池实现
		获取连接对象：conn = MySQL.getConn()
		释放连接对象;conn.close()或del conn
	"""
	#连接池对象
	__pool = None
	__mutex = threading.Lock()

	def __init__(self, settings = {}):
		"""
		数据库构造函数，从连接池中取出连接，并生成操作游标
		"""
		default_settings = {
			'host'	: Config.get('Database','Host'),
			'port'	: Config.getint('Database','Port'),
			'user'	: Config.get('Database','User'),
			'passwd': Config.get('Database','Passwd'),
			'db'	: Config.get('Database','Database')}
		default_settings.update(settings)

		self._conn = MySQL.__getConn(default_settings)
		self._cursor = self._conn.cursor()

	@staticmethod
	def __getConn(settings):
		"""
		@summary: 静态方法，从连接池中取出连接
		@return MySQLdb.connection
		"""
		MySQL.__mutex.acquire()
		if MySQL.__pool is None:
			__pool = PooledDB(creator=MySQLdb, mincached=5, maxcached=100, maxusage=1000,
							  host=settings['host'], port=settings['port'], 
							  user=settings['user'], passwd=settings['passwd'],
							  db=settings['db'], use_unicode=True,
							  charset='utf8', cursorclass=DictCursor)
		MySQL.__mutex.release()
		return __pool.connection()

	#######################################
	#
	# 事务
	#
	#######################################

	def begin(self):
		"""
		@summary: 开启事务
		"""
		self._conn.autocommit(0)

	def end(self,option='commit'):
		"""
		@summary: 结束事务
		"""
		if option=='commit':
			self._conn.commit()
		else:
			self._conn.rollback()

	def dispose(self,isEnd=1):
		"""
		@summary: 释放连接池资源
		"""
		if isEnd==1:
			self.end('commit')
		else:
			self.end('rollback');
		self._cursor.close()
		self._conn.close()


	#######################################
	#
	# 获取记录
	#
	#######################################

	def list(self, sql, param=None):
		"""
		@summary: 执行查询，并取出所有结果集
		@param sql:查询ＳＱＬ，如果有查询条件，请只指定条件列表，并将条件值使用参数[param]传递进来
		@param param: 可选参数，条件列表值（元组/列表）
		@return: result list/boolean 查询到的结果集
		"""
		if param is None:
			count = self._cursor.execute(sql)
		else:
			count = self._cursor.execute(sql, param)

		if count > 0:
			result = self._cursor.fetchall()
		else:
			result = []

		return result


	def get(self, sql, param=None):
		"""
		@summary: 执行查询，并取出第一条
		@param sql:查询ＳＱＬ，如果有查询条件，请只指定条件列表，并将条件值使用参数[param]传递进来
		@param param: 可选参数，条件列表值（元组/列表）
		@return: result list/boolean 查询到的结果集
		"""
		if param is None:
			count = self._cursor.execute(sql)
		else:
			count = self._cursor.execute(sql, param)

		if count > 0:
			result = self._cursor.fetchone()
		else:
			result = False

		return result


	#######################################
	#
	# 插入记录
	#
	#######################################

	def save(self, sql, value):
		"""
		@summary: 向数据表插入一条记录
		@param sql:要插入的ＳＱＬ格式
		@param value:要插入的记录数据tuple/list
		@return: insertId 受影响的行数
		"""
		count = self._cursor.execute(sql,value)
		# save mulit value
		#count = self._cursor.executemany(sql,value)
		return count

	def getInsertId(self):
		"""
		获取当前连接最后一次插入操作生成的id, 如果没有则为０
		"""
		self._cursor.execute("SELECT @@IDENTITY AS id")
		result = self._cursor.fetchall()
		return result[0]['id']


	#######################################
	#
	# 更新记录
	#
	#######################################

	def update(self, sql, param=None):
		"""
		@summary: 更新数据表记录
		@param sql: SQL格式及条件，使用(%s,%s)
		@param param: 要更新的  值 tuple/list
		@return: count 受影响的行数
		"""
		return self.__query(sql, param)


	#######################################
	#
	# 删除记录
	#
	#######################################

	def delete(self, sql, param=None):
		"""
		@summary: 删除数据表记录
		@param sql: ＳＱＬ格式及条件，使用(%s,%s)
		@param param: 要删除的条件 值 tuple/list
		@return: count 受影响的行数
		"""
		return self.__query(sql, param)


	def __query(self, sql, param=None):
		if param is None:
			count = self._cursor.execute(sql)
		else:
			count = self._cursor.execute(sql,param)
		return count





if __name__ == "__main__":
	db = MySQL({
		'host'	: 'localhost',
		'port'	: 3306,
		'user'	: 'root',
		'passwd': '1q2w3e',
		'db'	: 'videos'})

	for i in db.list('SHOW TABLES'):
		tab = i.values()[0]
		print "===============%s==============" % tab
		for y in db.list('DESC ' + tab):
			print "%s %s %s" % (y['Field'], y['Type'], y['Key'])

	for i in db.list('SELECT * FROM `app`'):
		print i
	pass
