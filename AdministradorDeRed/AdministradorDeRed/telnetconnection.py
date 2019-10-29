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
		return None, 'Interrupcion: ' + str(eoferror)

	return tn, mssg


def obtener_subredes_telnet(tn, mask = True, tipo = None):
	routeTable = b""
	#Expresion regular de una subred
	patron = None
	if mask:
		patron = re.compile('\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}/\\d{1,2}')
	else:
		patron = re.compile('\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}')

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
	tn.read_until(b'\n', 2)
	hostname = tn.read_until(b'#', 2).decode('utf8')
	return hostname[0:len(hostname)-1]


def obtener_archivo_configuracion(tn, tftpServerHost, fileName):
	lh = tftpServerHost.encode('utf-8')
	fn = fileName.encode('utf-8')

	tn.write(b'copy running-config tftp:\n')
	
	tn.read_until(b'Address or name of remote host []? ', 5)
	tn.write(lh + b'\n')
	
	tn.read_until(b'Destination filename ', 5)
	tn.write(fn + b'\n')

	tn.read_until(b'#', 30)
	print('Se obtuvo archivo: ' + fileName)
	return True

def restablecer_router_tftp(tn, tftpServerHost, filePath):
	lh = tftpServerHost.encode('utf-8')
	fp = filePath.encode('utf-8')

	tn.write(b'copy tftp: running-config\n')

	tn.read_until(b'Address or name of remote host []? ', 5)
	tn.write(lh + b'\n')

	tn.read_until(b'Source filename []? ', 5)
	tn.write(fp + b'\n')

	tn.read_until(b'Destination filename ', 5)
	tn.write(b'running-config\n')

	tn.read_until(b'#', 30)
	tn.write(b'reload\n')
	tn.read_until(b'[confirm]', 5)
	tn.write(b'\n')
	
	print('Se restablecio archivo: ' + filePath)
	
	return True