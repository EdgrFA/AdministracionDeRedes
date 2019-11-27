import socket
import sys

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = ('192.168.0.2', 9001)
sock.bind(server_address)
print("Servidor iniciado en puerto 9001.")

while(True):
	data, address = sock.recvfrom(4096)
	print('datagram received {} bytes from {}'.format(len(data), address))

	if data:
		sent = sock.sendto(data, address)