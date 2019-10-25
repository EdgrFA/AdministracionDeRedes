#!/usr/bin/env python3
import fileinput
import socket
import sys

data = ""
for line in fileinput.input():
    data += line

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('localhost', 8081)

try:
    # Send data
    sent = sock.sendto(data.encode('utf-8'), server_address)

finally:
    print('closing socket')
    sock.close()