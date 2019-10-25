#!/usr/bin/env python3
import fileinput
import socket
import sys
import re


trap = ''
for line in fileinput.input():
	trap += line

patHost = re.compile('\\[[^\\]]+\\]')
patInterfaz = re.compile('FastEthernet[0-9]+/[0-9]+')
patTexto = re.compile('\\"[^\\"]+\\"')
host = patHost.findall(trap)
interfaz = patInterfaz.findall(trap)
mensaje = patTexto.findall(trap)

strHost = 'Host' + host[0] + ': '
data = strHost + '' + interfaz[0]
for m in mensaje:
	data += ", " + m.replace('\"', '')

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('localhost', 8081)

try:
    # Send trap
    sent = sock.sendto(data.encode('utf-8'), server_address)

finally:
	sock.close()