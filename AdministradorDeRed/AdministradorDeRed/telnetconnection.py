import telnetlib
import socket
import re

def conectar_telnet(ip, passwordTelnet, passwordEnable = None):
	tn = None
	mssg = None
	try:
		#Conectar Telnet
		tn = telnetlib.Telnet(ip, 23, 4)
		#tn.set_debuglevel(9)
		tn.read_until(b'Password: ', 5)
		tn.write(passwordTelnet.encode('utf-8') + b'\n')
		respuesta = tn.read_until(b'>', 1)
		#Comprobar que se establecio conexion
		if respuesta.find(b'Password: ') != -1:
			print('Telnet: Contrasena incorrecta')
			tn.close()
			return None, 'Telnet: Contraseña incorrecta.'
		mssg = 'Telnet: Conexion exitosa con ' + ip

		if passwordEnable != None :
			#Habilitar modo enable
			tn.write(b'enable\n')
			tn.read_until(b'Password: ', 1)
			tn.write(passwordEnable.encode('utf-8') + b'\n')
			respuesta = tn.read_until(b'#', 1)
			if respuesta.find(b'Password: ') != -1:
				print('Telnet(enable): Contrasena incorrecta')
				tn.close()
				return None, 'Telnet(enable): Contraseña incorrecta.'
			mssg = 'Telnet(enable): Conexion exitosa con ' + ip

	except OSError as oserr:
		#Para No route to host 113 y timeout
		return None, 'Interrupcion(' + ip + '): ' + str(oserr)

	except EOFError as eoferror:
		#Conexion terminada
		return None, 'Interrupcion: ' + eoferror

	return tn, mssg


def obtener_subredes_telnet(tn, tipo = None):
	routeTable = b""
	#Expresion regular de una subred
	patron = re.compile('\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}/\\d{1,2}')
	#Filtrar subredes
	if tipo == None:
		tn.write(b'show ip route list subnets | exclude L        \n')
	elif tipo == 'L':
		tn.write(b'sh ip route connected | include L       \n')

	while True:
		routeTable += tn.read_until(b' --More-- ', 1)
		if routeTable.find(b" --More-- ") != -1:
			routeTable = routeTable.replace(b" --More-- ", b"")
			tn.write(b' ')
			continue
		break
	routeTable = routeTable.decode('utf8')
	return set(patron.findall(routeTable))

def obtener_nombre_host(tn):
	tn.write(b'\n')
	hostname = 'equisde'