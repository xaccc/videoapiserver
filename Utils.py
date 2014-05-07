#coding=utf-8
#-*- encoding: utf-8 -*-

from datetime import date,datetime,timedelta

import uuid, hashlib, json
import dateutil.tz, dateutil.parser



class MyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.replace(tzinfo=dateutil.tz.tzlocal()).strftime('%Y-%m-%dT%H:%M:%SZ%z')
        elif isinstance(obj, date):
            return obj.replace(tzinfo=dateutil.tz.tzlocal()).strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)

def json_dumps(data):
    return json.dumps(data, cls=MyJSONEncoder, sort_keys=False)

def UUID():
    return str(uuid.uuid4()).replace('-','')

def MD5(data):
    return hashlib.md5(data).hexdigest()


if __name__ == "__main__":
    print "json_dump: %s" % json_dump({'hello':'world', 'now': datetime.now()})
    print "UUID: %s" % UUID()
    print "MD5: %s" % MD5('helloworld')
