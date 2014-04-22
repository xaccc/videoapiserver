#!/usr/bin/python
#coding=utf-8
#-*- encoding: utf-8 -*-

import json
import urllib
import urllib2

def dwz(url):
    print "dwz: %s" % url
    req = urllib2.Request("http://dwz.cn/create.php")
    opener = urllib2.build_opener()
    response = opener.open(req, urllib.urlencode({'url': url}))
    d = json.loads(response.read())
    if d['status'] != 0:
        return None

    return str(d['tinyurl'])


if __name__ == '__main__':
    '''Test Code'''
    print dwz('https://github.com/hit9/CURD.py/blob/master/CURD.py')