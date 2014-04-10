# -*- encoding: utf-8 -*-

from CURD import Database, Model, Field, PrimaryKey, ForeignKey, Fn

Database.config(host='localhost', db='videos', user='root', passwd='1q2w3e')


class Validate(Model):
	"""
	短信验证码
	"""
	mobile = Field()
	code = Field()
	device = Field()
	valid_time = Field()
	create_date = Field()


class User(Model):
	"""
	用户信息
	"""
	id = PrimaryKey()
	mobile = Field()
	login = Field()
	password = Field()
	email = Field()
	name = Field()


class Session(Model):
	id = PrimaryKey()
	user_id = ForeignKey(User.id)
	device = Field()
	valid_time = Field()
	create_time = Field()


class Upload(Model):
	id = PrimaryKey()
	owner_id = ForeignKey(User.id)
	length = Field()
	saved = Field()
	create_time = Field()
	update_time = Field()


if __name__ == "__main__":
	for item in Upload.findall():
		print item.create_time
