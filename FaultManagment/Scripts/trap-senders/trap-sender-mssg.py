#!/usr/bin/env python3
import fileinput
import socket
import sys
import re


trap = ''
for line in fileinput.input():
	trap += line

patHost = re.compile('\\[[^\\]]+\\]')
patTexto = re.compile('\\"[^\\"]+\\"')
mensaje = patTexto.findall(trap)
host = patHost.findall(trap)

data = 'Host' + host[0] + ': '
isFirst = True
for m in mensaje:
	if isFirst:
		data += m.replace('\"', '')
		isFirst = False
		continue
	data += ", " + m.replace('\"', '')

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('localhost', 8081)

try:
    # Send trap
    sent = sock.sendto(data.encode('utf-8'), server_address)

finally:
	sock.close()