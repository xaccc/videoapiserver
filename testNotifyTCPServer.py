#coding=utf-8
#-*- encoding: utf-8 -*-

import tornado.ioloop
import tornado.iostream
import socket
import struct

import NotifyTCPServer


def readPacketHeader():
	stream.read_bytes(NotifyTCPServer.PACKET_HEADER_LEN, parsePacketHeader)


def parsePacketHeader(data):
	sign,cmd,bodySize = struct.unpack('>2sHH', data)
	print "Sign: %s, Command: %s, Size: %s" % (sign,cmd,bodySize)
	command=cmd
	stream.read_bytes(bodySize, parsePacketBody)


def parsePacketBody(data):
	print "Data: %s" % str(data)

	if command == NotifyTCPServer.NOTIFY_COMMAND_PING:
		send_ping(data)

	readPacketHeader()


def send_register(userKey):
	send_packet(NotifyTCPServer.NOTIFY_COMMAND_REGISTER, userKey)

def send_ping(msg):
	send_packet(NotifyTCPServer.NOTIFY_COMMAND_PING, msg)

def send_packet(cmd, msg):
	data = bytes(msg)
	stream.write(struct.pack(">2sHH", "NT", cmd, len(data)))
	stream.write(data)




def send_request():
	readPacketHeader()
	send_register('591410cbf9614cbf9aaac4a871ddb466')



command=0
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
stream = tornado.iostream.IOStream(s)
stream.connect(("localhost", 9002), send_request)
tornado.ioloop.IOLoop.instance().start()