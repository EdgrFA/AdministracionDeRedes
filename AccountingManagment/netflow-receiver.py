import socket
import sys
import codecs
from netflow import parse_packet

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address = ('', 2056)
print('starting up on {} port {}'.format(*server_address))
sock.bind(server_address)

while True:
    print('\nwaiting to receive message')
    data, address = sock.recvfrom(65536)

    print('received {} bytes from {}'.format(
        len(data), address))
    data = data.decode('utf-8', 'ignore')
    print(data)
